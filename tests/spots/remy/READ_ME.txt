Description des scripts écrit durant le stage de M2 de 2014
Auteur : Rémy Le Breton

Chemin des fichiers décrit : ~/LSST/lsst/py/tests/spots/remy/

A faire : vérifier les fonctions FOCUS_EQ_EST_OUEST et FOCUS_EQ_VERTICAL.

*.fits : 
       Des images tests, peuvent être effacées.

*.data :

       default_pos.data : contient des coordonnées par défault. On peut les lire pour y aller ou les écrires pour les changer si le focus est meilleur pour une autre position.

*.py :

     analyse_vke.py : analogue à la fonctions analyse_vke dans fonctions.py.

     fit_profil.py : Pour "fitter" un spot avec un profil gaussien en 2D. Attention : spécifier les fichiers à lire.

     focus.py : procède au focus en plusieurs étapes. Utilise les fonctions de fonctions.py.
     
     fonctions.py : comprend les fonctions que j'ai écrite pour le focus, déplacments suivant un certain axes...

     fonctions_test.py : script pour tester une fonction créée avant de l'inclure dans fonctions.py.

     init_mov_cam.py : initialise les moteurs et la caméra.

     __init__.py : je ne me souviens pas avoir créé ce fichiers.

     intensite.py : pour prendre des images à des intensités différentes. Ne marche pas si la caméra a un auto-gain !

     test_home_pos.py : fait des home en boucle, et écrit les valeurs des ranges.

     test_home.py : fait des home en boucle, et regarde la position du maximum (le focus doit être fait à l'avance car on va à chque fois à la position par défaut.

     vke_beta.py : analogue à la fonctions VKE dans fonctions.py

     vke_n_steps.py : fait un aller retour dans un sens, puis dans l'autre, puis à nouveau dans le premier sens. Boucle sur ce principes.


dossiers :

	 focus : contient les images prises par la fonction FOCUS (voir fonctions.py).
	 
	 vke_beta : contient les images prises par la fonctions VKE (voir fonctions.py).

	 results : contient les données écrites par la fonctions SAVE_RESULTS (voir fonctions.py).
	 
	 test_home_pos : contient les données écrites par le script test_home_pos.py
