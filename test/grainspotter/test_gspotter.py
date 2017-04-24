from ImageD11 import indexing
myindexer = indexing.indexer()
myindexer.gspotter_add_card(['tthrange', '0 10'])
myindexer.gspotter_add_card(['etarange', '0 360'])
myindexer.gspotter_add_card(['omegarange', '-60 60'])
myindexer.gspotter_add_card(['domega', '0.5'])
myindexer.gspotter_add_card(['filespecs', 'd:/test/simAl.gve d:/test/simAltest.log'])
myindexer.gspotter_add_card(['cuts', '20 0.8 0.5'])
myindexer.gspotter_add_card(['eulerstep', '2'])
myindexer.gspotter_add_card(['uncertainties', '0.1 0.2 0.5'])
myindexer.gspotter_add_card(['nsigmas', '2'])
myindexer.gspotter_add_card(['minfracg', '1'])
myindexer.gspotter_add_card(['random', '100000'])
myindexer.gspotter_add_card(['genhkl', ''])
myindexer.gspotter_add_card(['spacegroup', '225'])
myindexer.gspotter_make_ini()
myindexer.gspotter_save_ini('d:/test/testing_simAl.ini')
myindexer.gspotter_run()
