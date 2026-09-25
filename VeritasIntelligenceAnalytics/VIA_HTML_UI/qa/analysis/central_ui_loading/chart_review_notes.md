# Central UI loading analysis chart review

The payload chart clearly shows the embedded Logo data URI as the dominant source bucket: approximately 1,396.5 KB versus 70.4 KB inline CSS, 23.3 KB inline JavaScript, and 36.0 KB other markup. The bar chart is legible. The donut labels for the smaller slices are crowded near the top; the next render should move the percentages into a compact legend or use a horizontal share bar.

The DOM distribution chart is legible and shows `.main` at 527 nodes (73.0%), `.sidebar` at 94 nodes (13.0%), two modals at 38 nodes each, and the main-content concentration in investment desk (140), bottom grid (138), and content grid (121). The labels and values are readable at the rendered resolution.

The DOM tag chart is readable and shows SPAN 162, DIV 123, PATH 55, BUTTON 50, and SVG 40 as the largest tag groups. It uses a horizontal ranking that avoids label overlap.

The deferral candidate chart is readable and highlights the 138-node bottom grid as the largest below-the-fold candidate, followed by two 38-node modals and the 22-node hidden UI Lab. It is suitable for explaining why lazy mounting and content-visibility should be evaluated separately.
