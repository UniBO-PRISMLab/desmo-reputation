Plot1:
x = Ratio of malign indexers o sources????
y = truth accuracy
hue1 = algorithm (noranking, ranking, kickout)
hue2 = uniform/bursty

    alpha = 0.5
    beta = 0.7


Plot2: 
x = Ratio of malign indexers
y = truth accuracy
hue1 = alpha
hue2 = uniform/bursty

    beta = 0.7
    algo = kickout

Plot3: 
x = Ratio of malign indexers
y = truth accuracy
hue1 = beta
hue2 = uniform/bursty

    alpha = 0.5
    algo = kickout


Plot 4/5:
x = epoch
y = kicout precision/kickout recall
hue = kickout threshold

Plot 6 (3d?):
x = alpha and beta
y = recall/precision
hue (multigraph) = kickout threshold

Oracles:
    - x: theta
    - y: time average
    - hue ranking/noranking
- MALICIOUS ORACLES?
