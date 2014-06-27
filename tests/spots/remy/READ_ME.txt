Description des scripts écrit durant le stage de M2
Auteur : Rémy Le Breton

Chemin des fichiers décrit : ~/LSST/lsst/py/tests/spots/remy/

*.fits : 
       Des images tests, peuvent être effacées.

*.data :

       default_pos.data : contient des coordonnées par défault. On peut les lire pour y aller ou les écrires pour les changer si le focus est meilleur pour une autre position.

*.py :

     analyse_vke.py : analogue à la fonctions analyse_vke dans fonctions.py.

     fit_profil.py : Pour "fitter" un spot avec un profil gaussien en 2D. Attention : spécifier les fichiers à lire.

     focus.py : procède au focus en plusieurs étapes. Utilise les fonctions de fonctions.py.
     
     focus_second_step.py : ancienne version du focus en plusieurs étapes. N'est plus utilisé.

     fonctions.py : comprend les fonctions que j'ai écrite pour le focus, déplacments suivant un certain axes...

     fonctions_test.py : script pour tester une fonction créée avant de l'inclure dans fonctions.py.

     init_mov_cam.py : initialise les moteurs et la caméra.

     __init__.py :

     intensite.py :

     move_and_test.py :

     profil.py :

     save_results.py :

     take_and_test.py :

     test_divers.py :

     test_home_pos.py :

     test_home.py :

     vke_beta.py :

     vke_n_steps.py :


dossiers :

	 focus : contient les images prises par la fonction FOCUS (voir fonctions.py).
	 
	 vke_beta : contient les images prises par la fonctions VKE (voir fonctions.py).

	 results : contient les données écrites par la fonctions SAVE_RESULTS (voir fonctions.py).
	 
	 test_home_pos : contient les données écrites par le script test_home_pos.py
