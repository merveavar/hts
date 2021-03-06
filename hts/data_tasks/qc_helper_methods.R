library(ggplot2); library(scales); library(RColorBrewer); library(plyr); library(MASS); library(reshape2); library(gridExtra);

# Pretty, but not perfect in case of red-green blindness:
#colors = c("darkblue", "blue", "turquoise", "green", "yellow", "red", "darkred")
#
#colors = c("darkblue", "blue", "turquoise", "green", "yellow", "magenta", "darkmagenta")

# Light orange to blue to black scale.
colors = c("black", "darkblue", "blue", "orangered3", "orange", "papayawhip")
# http://www.cookbook-r.com/Graphs/Colors_%28ggplot2%29/#a-colorblind-friendly-palette
cbbPalette <- c("#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7")
cbbPalette_wo_yellow <- c("#000000", "#E69F00", "#56B4E9", "#009E73", "#0072B2", "#D55E00", "#CC79A7")


tile_plot_x1x2 <- function(data, column, label, save){
data$x2 = factor(data$x2, levels = max(data$x2):min(data$x2))
data$x1 = factor(data$x1, levels = min(data$x1):max(data$x1))
data$tmp = data[,column]
p = ggplot(data, aes(x= x1, y= x2, fill=tmp), environment = environment()) 
p = p + geom_raster() + scale_fill_gradientn(colours = colors, name = column)
p = p + coord_fixed(ratio=1)
p = p + beautifier()
if (save == TRUE) {
ggsave(paste(pathImages, label, '_',column,'_x1x2.pdf', sep=''), width=12, height=8, dpi = 300)
}
return(p)
}

tile_plot_x1x2x3 <- function(data, column, save){
data$x2 = factor(data$x2, levels = max(data$x2):min(data$x2))
data$x1 = factor(data$x1, levels = min(data$x1):max(data$x1))
data$tmp = data[,column]
p = ggplot(data, aes(x= x1, y= x2, fill=tmp), environment = environment()) + facet_wrap(~x3)
p = p + geom_raster() + scale_fill_gradientn(colours = colors, name = column)
p = p + coord_fixed(ratio=1)
p = p + beautifier()
if (save == TRUE) {
ggsave(paste(pathImages, column, '_x1x2x3.pdf', sep=''), width=12, height=8, dpi = 300)
}
return(p)
}


tile_plot_x1x2x3_mark_conditionally <- function(data, column, save, condition, color){
    # Inspired by: # http://stackoverflow.com/questions/13258454/marking-specific-tiles-in-geom-tile-geom-raster/13260999#13260999
    data$x2 = factor(data$x2, levels = max(data$x2):min(data$x2))
    data$x1 = factor(data$x1, levels = min(data$x1):max(data$x1))
    p = ggplot(data, aes(x=x1,y=x2, fill=y), environment = environment()) + facet_wrap(~x3)
    p = p + geom_raster() + scale_fill_gradientn(colours=colors, name ="y")
    p = p + coord_fixed(ratio=1)
    p = p + beautifier()
    p = p + geom_point(data=subset(data, eval(parse(text=condition))), aes(x=x1,y=x2), size=0.8, color=color, shape=4)
    return(p)
}




get_label_positions <- function(x, thresholds){
  
  spread = diff(range(x))
  label_positions = (c(0, thresholds) + c(thresholds, 0))/2
  label_positions[[1]] = min(thresholds[[1]] - spread/10, min(x) + spread/5)
  label_positions[[length(label_positions)]] = max(thresholds[[length(thresholds)]] + spread/10, min(x) - spread/5)
  return(label_positions)
}


# Inspired by: http://minimaxir.com/2015/02/ggplot-tutorial/

beautifier <- function() {
# Generate the colors for the chart procedurally with RColorBrewer
palette <- brewer.pal("Greys", n=9)
color.background = NA
color.overlaid_background = "white"
color.grid.major = palette[2]
color.axis.text = palette[6]
color.axis.title = palette[7]
color.title = palette[9]

# Begin construction of chart
theme_bw(base_size=10) +

# Set the entire chart region to a light gray color
theme(panel.background=element_rect(fill='transparent',colour=color.background)) +
theme(plot.background=element_rect(fill='transparent',colour=color.background)) +
theme(panel.border=element_rect(color=color.background)) +

# Format the grid
theme(panel.grid.major=element_line(color=color.grid.major,size=.25)) +
theme(panel.grid.minor=element_blank()) +
theme(axis.ticks=element_blank()) +

# Format the legend.
# theme(legend.position="none") # Hiding the legend.
theme(legend.background = element_rect(fill=color.overlaid_background)) +
theme(legend.text=element_text(family="sans",size=10,face='italic',hjust=0,color=color.axis.title)) +
theme(legend.key=element_rect(fill=color.overlaid_background,color=color.overlaid_background)) +

# Set title and axis labels, and format these and tick marks
theme(plot.title=element_text(color=color.title, size=10, vjust=1.25)) +
theme(axis.text.x=element_text(size=9,color=color.axis.text,family="sans",angle=90,margin=margin(5,5,10,5,"pt"))) +
theme(axis.text.y=element_text(size=9,color=color.axis.text,family="sans",margin=margin(5,5,10,5,"pt"))) +
theme(axis.title.x=element_text(size=11,color=color.axis.title,vjust=0)) +
theme(axis.title.y=element_text(size=11,color=color.axis.title,vjust=1.25)) +

# No idea what strip is
theme(strip.background=element_rect(fill='transparent', colour=color.background))+
theme(strip.text.x=element_text(family="sans",size=10, angle=0))+
theme(strip.text.y=element_text(family="sans",size=10, angle=270))+

# Plot margins
theme(plot.margin = unit(c(0.35,0.2,0.3,0.35), "cm"))
}


# http://stackoverflow.com/questions/7549694/ggplot2-adding-regression-line-equation-and-r2-on-graph
lm_eqn = function(m) {

  l <- list(a = format(coef(m)[1], digits = 2),
      b = format(abs(coef(m)[2]), digits = 2),
      r2 = format(summary(m)$r.squared, digits = 3));

  if (coef(m)[2] >= 0)  {
    eq <- substitute(italic(y) == a + b %.% italic(x)*","~~italic(r)^2~"="~r2,l)
  } else {
    eq <- substitute(italic(y) == a - b %.% italic(x)*","~~italic(r)^2~"="~r2,l)
  }

  as.character(as.expression(eq));
}


# http://stats.stackexchange.com/questions/83826/is-a-weighted-r2-in-robust-linear-model-meaningful-for-goodness-of-fit-analys
r2ww <- function(x){
  SSe <- sum((x$w*x$resid)^2); #the residual sum of squares is weighted
  observed <- x$resid+x$fitted;
  # SSt <- sum((x$w*(observed-mean(observed)))^2); #the total sum of squares is weighted
  SSt <- sum((x$w*observed-mean(x$w*observed))^2)
  value <- 1-SSe/SSt;
  return(value);
}

r2 <- function(x){
  SSe <- sum((x$resid)^2);
  observed <- x$resid+x$fitted;
  SSt <- sum((observed-mean(observed))^2);
  value <- 1-SSe/SSt;
  return(value);
}

# Convert a robust rlm model to a string with linear model formula, r2 and r2ww
rlm_eqn = function(m) {

  l <- list(a = format(coef(m)[1], digits = 2),
      b = format(abs(coef(m)[2]), digits = 2),
      r2 = format(r2(m), digits = 3),
      r2ww = format(r2ww(m), digits = 3));

  if (coef(m)[2] >= 0)  {
    eq <- substitute(italic(y) == a + b %.% italic(x)*","~~italic(r)^2~"="~r2~","~~italic(r)^2~ww~"="~r2ww,l)
  } else {
    eq <- substitute(italic(y) == a - b %.% italic(x)*","~~italic(r)^2~"="~r2~","~~italic(r)^2~ww~"="~r2ww,l)
  }

  as.character(as.expression(eq));
}
