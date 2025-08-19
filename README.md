# multi-tenant-app
Idée de plateforme multi-tenant où chaque lycée crée son propre espace (tenant) pour gérer son établissement.

# Classes

Cette application gère les classes au sein de la plateforme PolyCampus.

## Fonctionnalités
- Création, modification et suppression de classes
- Association des classes aux écoles et aux étudiants

# Core

Application centrale contenant la logique et les modèles partagés de PolyCampus.

## Fonctionnalités
- Modèles et utilitaires communs à toutes les applications

## Enrollments

Gère les inscriptions des étudiants aux différentes classes et écoles.

## Fonctionnalités
- Inscription et désinscription des étudiants
- Gestion des périodes d’inscription

## Schools

Gère les établissements scolaires (lycées) sur la plateforme PolyCampus.

## Fonctionnalités
- Création et gestion des écoles
- Association des écoles aux classes et étudiants

## Students

Gère les informations et profils des étudiants.

## Fonctionnalités
- Création et gestion des profils étudiants
- Association des étudiants aux classes et écoles

## Users

Gère les utilisateurs et l’authentification sur la plateforme PolyCampus.

## Fonctionnalités
- Gestion des comptes utilisateurs
- Authentification et autorisations

