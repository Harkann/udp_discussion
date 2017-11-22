# Projet Réseau 2017

## Introduction

L'objectif était de réaliser un client de chat de groupe peer-to-peer.
Le langage choisi pour sa réalisation est **Python3**.
Les modules nécessaires pour l'execution du programme sont listés dans la section [Dépendances](##Dépendances)
Le programme se divise en plusieurs modules :
 * [client.py](###client.py)
 * [parser.py](###parser.py)
 * [tools.py](###tools.py)
 * [interface.py](###interface.py)

### Uttilisation
  * S'assurer de respecter les prérequis de [Dépendances](##Dépendances)
  * Configurer le client (config.py) ou garder celle par défaut
  * `python3 main.py`

## Fonctionalités

### Implémentées
  * Envoi/Réception de tous les TLVs de base.
  * Ignore les long hello pour le mauvais id
  * Ignore les TLVs > 7
  * GoAway en cas de :
    * déconnexion volontaire
    * 5 tentatives de Data sans Ack
  * Affichage des logs via le bouton «Logs»
  * Commandes (cf [interface.py](###interface.py))
  * Ne s'ajoute pas lui même comme voisin
  * Ajoute un délai aléatoire à l'envoi des Hello, Data et Neighbours.
      « En réseau on aime bien l'aléatoire » ~ JCH

### Non-implémentées
  * Support de l'ipv4
  * Séparation des Data trop longs en messages multiples

## Structure

### main
  Uniquement chargé de lancer le client
### client
  Lance les 3 threads qui composent le client :
  * Receiver : Chargé de recevoir les messages, de les parser et d'executer les actions appropriées (cf [parser.py](###parser.py))
  * Routine : Chargé d'envoyer les Hellos, les Neighbours et de rajouter des voisins à intervales réguliers
  * Dispatch : Chargé d'envoyer les Data aux voisins.

### interface
  Gestion de l'interface et du parsing des commandes

#### Commandes
  * **/help** : *affiche l'aide*
  * **/nick pseudo** : *Change le pseudo de l'uttilisateur pour «pseudo»*
  * **/me action** : *Équivalent du /me sur IRC/Skype/Discord*
  * **/connect adresse port** : *envoie un «Short Hello» à adresse:port* (adresse peut être une ipv6 ou un nom de domaine pointant vers une ipv6)
  * **/disconnect [all] [adresse port]** : *déconnecte tous les voisins (GoAway 3) ou seulement adresse:port*
  * **/close** : *Ferme le client* (même action de le bouton close ou quitter la fenêtre)

### tools
  Outils de formatage des messages et de résolution dns





## Dépendances
### Version de python
  Testé sous python 3.6.3
### Modules
 * socket
 * random
 * datetime
 * copy
 * struct
 * threading
 * ipaddress
 * tkinter
 * dns **(pas dans la lib standard, nécessite le paquet python3-dnspython sous Debian)**

## Bugs potentiels
  * Les threads pourraient potentielement rester bloqués idéfiniment si jamais on s'arrange pour que l'heure du système reste la même (en tout cas si l'issue est toujours d'actualité et si j'ai bien tout compris):  https://bugs.python.org/issue1607149

  * Il se peut d'un thread plante à la fermeture du programme, c'est du au fait que ma gestion de la fermeture des threads n'est pas gérée de façon très propre

## Remarques
  * Il semblerait que Tkinter rattrape toutes les exceptions dans les fonctions appelées par ses boutons... pratique pour débugger

## Crédits
  * https://stackoverflow.com/a/111160 : *Pour gérer la fermeture d'une fenêtre Tkinter*
