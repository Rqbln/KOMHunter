# **Analyse de l'Architecture de Développement Ultra-Rapide pour la Cybersécurité : Orchestration de la Méthode BMAD, de Cursor et du Protocole MCP pour le Projet KOMHunter**

La revitalisation d'un projet de cybersécurité inabouti tel que KOMHunter exige une rupture technologique avec les méthodes de développement conventionnelles. Le projet original, dont l'objectif principal réside dans la recherche proactive de menaces (threat hunting), se heurte souvent à la complexité de l'intégration des flux de données et à la maintenance de la cohérence architecturale sur le long terme.1 L'émergence de la méthode Breakthrough Method of Agile AI-Driven Development (BMAD), combinée à l'environnement de développement Cursor et au protocole Model Context Protocol (MCP), offre un cadre structurel capable de transformer radicalement la vélocité et la fiabilité de cette reconstruction.3 Cette analyse examine la pertinence de cet écosystème par rapport aux alternatives actuelles, en mettant l'accent sur la capacité à générer des preuves de fonctionnement tangibles et des suites de tests automatisées robustes.6

## **Fondements et Mécanismes de la Méthode BMAD**

La méthode BMAD se définit comme un framework universel pour le développement piloté par des agents d'intelligence artificielle. Contrairement au "vibe coding" — une approche souvent critiquée pour son manque de structure et son taux de rejet élevé lors de la montée en charge — BMAD impose une discipline agile stricte à l'interaction avec les modèles de langage (LLM).7 Le framework repose sur une équipe sophistiquée de plus de 21 agents spécialisés, chacun doté de commandes et de responsabilités distinctes, simulant ainsi une organisation de développement complète au sein d'une interface unique.3

### **L'Architecture Persona-Centrique**

Le succès de BMAD repose sur la segmentation des tâches par personas. Cette approche prévient la perte de contexte, un problème majeur où l'IA, agissant comme un assistant généraliste, tend à oublier les contraintes architecturales au fil de la conversation.4 Chaque agent BMAD, tel que l'Analyste, le Product Manager ou l'Architecte, opère à partir d'un fichier de configuration Markdown auto-contenu qui sert de plan opérationnel.3 Ces fichiers définissent l'identité de l'agent, ses capacités et ses interactions avec les autres membres de l'équipe virtuelle.3

| Persona | Rôle Stratégique | Artefacts de Sortie |
| :---- | :---- | :---- |
| **Analyste** | Étude de marché et idéation | Project Brief, Analyse concurrentielle |
| **Product Manager** | Spécifications fonctionnelles | PRD (Product Requirements Document) |
| **Architecte** | Design système et technique | Architecture Document, Schémas de données |
| **Scrum Master** | Gestion des tâches et stories | Sharded Epics, User Stories (.md) |
| **Developer** | Implémentation du code | Code source, Tests unitaires |
| **QA Engineer** | Validation et conformité | Rapports de tests, Matrices de traçabilité |

6

Cette structure permet une séparation claire des préoccupations. Par exemple, l'agent Architecte se concentre exclusivement sur les choix technologiques et le design du système, garantissant que l'agent Developer ne prend pas de décisions arbitraires qui pourraient compromettre la scalabilité de KOMHunter.4

### **Phases de Développement et Intelligence Adaptive**

La méthode BMAD introduit un cycle de vie en quatre phases : Analyse, Planification, Solutionnement et Implémentation.4 Une innovation majeure de la version v6 du framework est l'intelligence "Scale-Adaptive", qui ajuste automatiquement la profondeur de la planification en fonction de la complexité du projet.6 Pour un projet comme KOMHunter, qui passe d'un état inabouti à un outil de threat hunting complet, le framework peut passer d'un mode "Atomic Change" (pour corriger des bugs mineurs) à un mode "Enterprise" (pour concevoir des systèmes distribués complexes).6

Le passage de la planification à l'exécution s'effectue via le "Context-Engineered Development". Cette discipline optimise les instructions fournies aux agents de développement en injectant le contexte complet du projet directement dans leurs tâches.7 Le Scrum Master transforme les épopées (epics) en "Story Files" hautement détaillés qui préservent l'intention architecturale et les critères d'acceptation, éliminant ainsi les hallucinations fréquentes lors de la génération de code sans contexte.7

## **L'Écosystème Cursor et le Model Context Protocol (MCP)**

Pour réaliser le plein potentiel de BMAD, l'utilisation de l'IDE Cursor est un catalyseur indispensable. Cursor n'est pas simplement un éditeur de texte, mais un environnement de développement "AI-first" construit sur un fork de VS Code, intégrant nativement des fonctionnalités de compréhension de codebase et de refactorisation multi-fichiers.13

### **Le Protocole MCP : Un Port Universel pour l'IA**

Le Model Context Protocol (MCP) agit comme une interface standardisée connectant les applications d'IA à des sources de données et des outils externes.5 Il permet à Cursor de dépasser les limites de l'analyse statique du code en lui donnant accès à un écosystème de serveurs MCP spécialisés.5 Pour le développement de KOMHunter, cette connectivité est cruciale car elle permet aux agents d'IA d'interagir directement avec l'infrastructure sur laquelle l'outil sera déployé.5

L'architecture MCP se compose de deux parties : les serveurs, qui exposent les données et les outils, et les clients (comme Cursor), qui consomment ces capacités.5 En intégrant des serveurs MCP pour PostgreSQL, GitHub ou même Slack, le développeur peut orchestrer des flux de travail où l'IA met à jour les tickets Jira, vérifie les schémas de base de données en temps réel ou notifie l'équipe des succès de déploiement, le tout sans quitter l'interface de développement.16

### **Intégration de Google Chrome DevTools MCP**

L'utilisation du serveur chrome-devtools-mcp transforme Cursor en un environnement de test et de débogage dynamique.20 Cet outil permet aux agents d'IA de contrôler et d'inspecter une instance réelle de Google Chrome, accédant ainsi à l'intégralité de la puissance de Chrome DevTools.20

| Capacité | Fonctionnalité pour KOMHunter | Impact sur la POF |
| :---- | :---- | :---- |
| **Inspection du DOM** | Vérification de l'interface de monitoring | Assurance de la visibilité des alertes |
| **Traces Réseau** | Analyse du trafic de beaconing simulé | Preuve de détection des communications C2 |
| **Logs de Console** | Capture des erreurs JavaScript en temps réel | Débogage immédiat de l'UI |
| **Audits Lighthouse** | Optimisation des performances de rendu | Garantie de réactivité sous charge massive |
| **Captures d'écran** | Documentation visuelle des détections | Preuve historique de fonctionnement |

20

Cette intégration est particulièrement pertinente pour KOMHunter, car elle permet de valider les fonctionnalités de l'outil dans un environnement contrôlé mais réel. L'IA peut automatiser des scénarios d'attaque par navigateur, capturer les réponses de l'outil et ajuster le code de détection en conséquence, créant ainsi une boucle de rétroaction ultra-rapide.20

## **Application de BMAD au Projet KOMHunter**

KOMHunter se positionne dans le domaine critique du threat hunting, dont l'objectif est d'identifier les menaces furtives (exploits zero-day, mouvements latéraux, persistances) qui échappent aux outils de sécurité traditionnels.1 Reprendre ce projet avec BMAD nécessite une compréhension profonde de la sémantique des attaques cybernétiques.1

### **Traduction des Tactiques de Chasse en Exigences Logicielles**

Le threat hunting repose sur l'élaboration d'hypothèses basées sur l'intelligence des menaces et le comportement des adversaires.25 L'agent Analyste de BMAD peut être utilisé pour ingérer les frameworks comme MITRE ATT\&CK et définir les capacités prioritaires de KOMHunter.11

L'analyse de la sécurité proactive se concentre sur plusieurs vecteurs clés que KOMHunter doit adresser :

* **Activité PowerShell suspecte** : Les attaquants utilisent souvent des scripts obfusqués pour exécuter du code en mémoire sans déclencher d'alertes antivirus.27  
* **Mouvements latéraux** : L'utilisation anormale de protocoles comme RDP ou SMB pour se déplacer d'un système à un autre.27  
* **Comportement de beaconing** : Des communications régulières et discrètes vers un serveur de commande et contrôle (C2).27

L'agent Product Manager traduit ces tactiques en exigences fonctionnelles (FR) et non-fonctionnelles (NFR) dans le PRD, tandis que l'Architecte conçoit les modules de capture et de corrélation de données nécessaires, comme l'intégration de flux Zeek ou Suricata pour le monitoring réseau.7

### **Développement Itératif et "Preuve de Fonctionnement" (POF)**

La méthode BMAD privilégie le "Simple Path" pour les petites fonctionnalités ou le "Full Planning Path" pour les architectures complexes.6 Pour KOMHunter, chaque module de détection peut être développé comme une itération de sprint gérée par le Scrum Master.

La preuve de fonctionnement est établie à travers le module QA de BMAD. Le framework offre deux options de test 6 :

1. **Quinn (QA)** : Inclus dans le module core, cet agent génère rapidement des tests unitaires et d'intégration basés sur des patterns standards, idéal pour expédier des fonctionnalités rapidement.6  
2. **Test Architect (TEA)** : Module optionnel pour les projets critiques, TEA propose une stratégie de test basée sur les risques, des portes de qualité (quality gates) et des évaluations de conformité.6

Dans le contexte de KOMHunter, TEA peut être utilisé pour valider que les algorithmes de détection ne génèrent pas un volume excessif de faux positifs, ce qui est une mesure de performance vitale pour les équipes de sécurité.1

## **Analyse Comparative des Méthodes de Développement IA**

Bien que BMAD propose une structure complète, il est essentiel de la confronter aux autres méthodologies disponibles pour déterminer s'il s'agit réellement de la "meilleure" approche pour KOMHunter.

### **BMAD vs. Spec-kit**

Spec-kit, souvent associé à l'écosystème GitHub, se concentre sur un flux "spec-to-code" très tactique.9

* **Spec-kit** excelle dans l'échafaudage rapide de code à partir de spécifications versionnées, ce qui est très efficace pour les développeurs individuels travaillant sur des composants isolés.9  
* **BMAD**, en revanche, adopte une philosophie stratégique et orientée équipe, couvrant l'intégralité du cycle de vie du projet.9

| Caractéristique | BMAD Method | Spec-kit |
| :---- | :---- | :---- |
| **Philosophie** | Stratégique et orientée équipe | Tactique et centrée développeur |
| **Portée** | Cycle complet (Idée à QA) | Niveau fonctionnalité (Spec à code) |
| **Public Cible** | Équipes agiles complètes | Développeurs individuels |
| **Gestion du Contexte** | Sharding de documents et agents | Spécifications exécutables |
| **Validation** | Agent QA dédié et TEA | Tests intégrés aux specs |

9

L'approche hybride recommandée consiste à utiliser les agents BMAD pour la planification stratégique (Analyste, PM, Architecte) et à utiliser les commandes tactiques de Spec-kit pour l'implémentation rapide des composants spécifiques.9

### **BMAD vs. Aider et TDD**

Aider est souvent décrit comme un partenaire de Test-Driven Development (TDD).9 Il est particulièrement puissant pour les cycles de rétroaction courts où le développeur écrit un test et demande à l'IA de corriger le code pour qu'il passe.9

* **Points forts d'Aider** : Intégration profonde avec Git (commits automatiques), capacité à corriger les erreurs de linting et de test en autonomie, et cartographie du codebase pour comprendre le contexte global.9  
* **Limites** : Sans une structure comme BMAD, Aider peut parfois "écraser" des modifications si plusieurs instances d'agents travaillent sur le même fichier, et il manque de la couche de planification stratégique nécessaire pour les grands projets.9

L'utilisation du TDD avec l'IA est une fondation solide car elle fournit un feedback déterministe à des modèles qui sont par nature probabilistes.28 Pour KOMHunter, coupler la discipline TDD d'Aider avec la gestion de projet de BMAD permettrait de maintenir une haute qualité de code tout en gardant une vision à long terme.9

### **Alternatives "Low-Code" et Prototypage Rapide**

Pour les phases initiales de prototypage ou pour des outils internes simples, des plateformes comme Bolt.new, Replit Agent ou Lovable offrent une rapidité imbattable.15

* **Bolt.new** : Permet de générer et de déployer des applications React complètes en quelques minutes, gérant le frontend, le backend et la base de données de manière transparente.33  
* **Replit Agent** : Assemble une application entière à partir d'une description textuelle, incluant l'authentification et l'hébergement.15

Cependant, ces outils sont souvent des "boîtes noires" difficiles à intégrer dans des codebases existants ou matures.15 Pour un projet comme KOMHunter, qui nécessite des interactions de bas niveau avec le système d'exploitation et des protocoles réseau spécifiques, la flexibilité offerte par Cursor et l'architecture "Agent-as-Code" de BMAD est supérieure.12

## **Efficacité Opérationnelle et Retours d'Expérience**

L'adoption de BMAD n'est pas sans défis. Les discussions au sein des communautés de développeurs révèlent un clivage entre les partisans de la structure et ceux qui craignent une perte de vélocité due à la complexité du framework.34

### **Productivité et Coût de l'Orchestration**

L'utilisation d'une équipe multi-agents comme celle proposée par BMAD peut multiplier la latence et les coûts par 2 à 4 par rapport à un agent unique.36 Pour un développeur solo, la gestion de 21 agents peut sembler excessive pour des tâches simples. C'est ici que l'intelligence "Scale-Adaptive" de BMAD prend tout son sens, en permettant de sauter les étapes de planification lourdes pour les changements atomiques.6

Néanmoins, la discipline imposée par BMAD réduit drastiquement les retravaux. Les statistiques de l'industrie suggèrent que le TDD seul réduit les taux de défauts de 40%, et l'utilisation de frameworks structurés permet d'éviter les nosedives de qualité qui surviennent lorsque l'IA génère du code dupliqué ou incohérent.9

### **L'Importance de la Surveillance Humaine**

Un risque identifié dans les discussions d'ingénierie est la "surcharge cognitive" liée à la surveillance de plusieurs agents produisant des dizaines de Pull Requests par semaine.29 Si aucun humain ne peut raisonnablement réviser ce volume de code, la qualité globale peut se dégrader.29 La méthode BMAD tente de résoudre ce problème en utilisant des agents pour réviser d'autres agents, mais la supervision humaine reste le dernier rempart contre les bugs subtils ou les erreurs de logique métier.18

| Avantage | Mécanisme BMAD | Impact sur KOMHunter |
| :---- | :---- | :---- |
| **Handoff Clair** | Artifacts et notes de transfert explicites | Pas de perte d'info entre le design et le code |
| **Auditabilité** | Documentation comme source unique de vérité | Facilité de maintenance pour les futurs contributeurs |
| **Consistance** | Personas spécialisés évitant le changement d'humeur de l'IA | Code homogène sur l'ensemble du projet |
| **Réduction de l'Hallucination** | Specs strictes agissant comme contrat | Moins de temps passé à débugger des fonctions inutiles |

4

## **Mise en Œuvre Pratique pour KOMHunter**

Pour redémarrer le développement de KOMHunter de manière ultra-rapide avec BMAD et Cursor, une configuration rigoureuse est nécessaire dès le premier jour.

### **Étape 1 : Installation et Configuration du Framework**

L'installation de BMAD (version v6-alpha recommandée) s'effectue via npm 6 :

Bash

npx bmad-method install

Pendant le processus, il est crucial de sélectionner l'IDE Cursor et d'activer le "Document Sharding" pour optimiser la fenêtre de contexte de l'IA.11 L'initialisation du projet se fait ensuite par la commande \*workflow-init au sein de l'éditeur.11

### **Étape 2 : Définition des Règles de l'Agent (.cursorrules)**

Pour maintenir la cohérence, l'utilisation des fichiers .cursorrules ou .mdc est impérative.38 Ces fichiers permettent de définir des comportements permanents pour l'IA, comme l'obligation d'utiliser des types stricts, de suivre les patterns de sécurité ou d'automatiser la génération de documentation.38

Une méta-règle efficace pour KOMHunter pourrait inclure des directives sur la gestion des erreurs et la performance, essentielles pour un outil de monitoring en temps réel. Le framework BMAD propose des outils pour générer automatiquement ces règles à partir de la structure de votre projet.41

### **Étape 3 : Intégration des Outils de Diagnostic**

L'ajout des serveurs MCP pour le diagnostic système et réseau permet d'apporter une preuve de fonctionnement constante. En configurant chrome-devtools-mcp, le développeur peut demander à Cursor :

"Ouvre l'application KOMHunter dans le navigateur, simule l'ingestion d'un log PowerShell suspect et vérifie si l'alerte apparaît dans la console et sur l'interface graphique.".18

Si le test échoue, l'agent peut inspecter les logs réseau et la console de rendu pour identifier si le problème vient du backend (API) ou du frontend (UI), et appliquer les correctifs immédiatement.18

## **Évaluation Finale : BMAD est-elle la Meilleure Méthode?**

La réponse à cette question dépend de l'équilibre entre la rigueur nécessaire et la vitesse d'exécution souhaitée.

### **Pourquoi BMAD est Supérieur pour KOMHunter**

Pour un projet de cybersécurité complexe, BMAD est effectivement la méthode la plus robuste pour plusieurs raisons :

1. **Fiabilité Architecturale** : Le threat hunting demande une corrélation de données précise. La séparation des rôles (Architecte vs. Dev) garantit que le moteur de corrélation est conçu selon des principes solides avant d'être codé.4  
2. **Traçabilité** : Chaque ligne de code est liée à une User Story, elle-même issue d'un PRD. En cas de bug de détection, il est facile de remonter à l'exigence initiale pour voir si l'erreur vient de la spécification ou de l'implémentation.7  
3. **Scalabilité de l'Équipe** : Même pour un développeur solo, simuler une équipe permet de couvrir des angles morts (sécurité, performance, UX) que l'on aurait tendance à négliger en codage libre.4

### **Les Points de Vigilance**

Cependant, BMAD n'est pas sans friction :

* **Courbe d'apprentissage** : Maîtriser les 50+ workflows et les commandes des agents prend du temps (estimé à 2-3 jours pour une maîtrise initiale).6  
* **Consommation de Tokens** : L'échange constant entre les agents pour la planification et la revue de code peut s'avérer coûteux en jetons d'API (OpenAI/Claude).36  
* **Risque de Sur-Ingénierie** : Pour des outils extrêmement simples, BMAD pourrait introduire une bureaucratie logicielle inutile.35

### **Verdict et Recommandation**

Pour KOMHunter, dont l'échec initial était probablement lié à un manque de structure et de continuité, **la méthode BMAD est indiscutablement le meilleur choix stratégique actuellement disponible en 2026**.3 Elle transforme le développement d'un "projet passion" en un processus d'ingénierie rigoureux, tout en exploitant la vitesse phénoménale offerte par Cursor et le protocole MCP.14

Le développeur devrait adopter une **approche hybride** :

1. Utiliser **BMAD (Full Planning Path)** pour établir le PRD, l'Architecture et le Backlog initial de KOMHunter.6  
2. Utiliser **Cursor et MCP** pour l'implémentation quotidienne, en s'appuyant sur les capacités de navigation de l'agent pour valider l'UI et le réseau.22  
3. Utiliser **Aider ou les agents de développement de Cursor** en mode TDD pour les corrections rapides de bugs, tout en gardant le Scrum Master de BMAD comme garant de l'état du sprint.9  
4. Implémenter systématiquement le module **TEA (Test Architect)** pour les composants de détection de menaces afin d'assurer une couverture de test de niveau entreprise.6

En suivant ce schéma, KOMHunter peut non seulement être finalisé en un temps record, mais aussi atteindre un niveau de qualité et de fonctionnalité prêt pour une utilisation en production réelle, prouvé par des tests automatisés et des démonstrations visuelles continues.12

#### **Sources des citations**

1. What is Threat Hunting in cybersecurity? \- OffSec, consulté le février 2, 2026, [https://www.offsec.com/cyberversity/threat-hunting/](https://www.offsec.com/cyberversity/threat-hunting/)  
2. 4 Types of Threat Hunting Tools & Top 8 Tools to Know in 2025 | CyCognito, consulté le février 2, 2026, [https://www.cycognito.com/learn/threat-hunting/threat-hunting-tools/](https://www.cycognito.com/learn/threat-hunting/threat-hunting-tools/)  
3. BMAD-METHOD™ : Building Custom AI Agents with BMB and Google AntiGravity \- Medium, consulté le février 2, 2026, [https://medium.com/@visrow/bmad-method-building-custom-ai-agents-with-bmb-and-google-antigravity-54ac96024e94](https://medium.com/@visrow/bmad-method-building-custom-ai-agents-with-bmb-and-google-antigravity-54ac96024e94)  
4. BMAD: The Agile Framework That Makes AI Actually Predictable \- DEV Community, consulté le février 2, 2026, [https://dev.to/extinctsion/bmad-the-agile-framework-that-makes-ai-actually-predictable-5fe7](https://dev.to/extinctsion/bmad-the-agile-framework-that-makes-ai-actually-predictable-5fe7)  
5. Model Context Protocol (MCP) | Cursor Docs, consulté le février 2, 2026, [https://cursor.com/docs/context/mcp](https://cursor.com/docs/context/mcp)  
6. bmad-code-org/BMAD-METHOD: Breakthrough Method for ... \- GitHub, consulté le février 2, 2026, [https://github.com/bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)  
7. The BMAD Method: A Framework for Spec Oriented AI-Driven Development, consulté le février 2, 2026, [https://recruit.group.gmo/engineer/jisedai/blog/the-bmad-method-a-framework-for-spec-oriented-ai-driven-development/](https://recruit.group.gmo/engineer/jisedai/blog/the-bmad-method-a-framework-for-spec-oriented-ai-driven-development/)  
8. Formation au Vibe Coding \- Ambient IT, consulté le février 2, 2026, [https://www.ambient-it.net/formation/vibe-coding/](https://www.ambient-it.net/formation/vibe-coding/)  
9. Beyond the Vibe: Why AI Coding Workflows Need a Framework, consulté le février 2, 2026, [https://dzone.com/articles/beyond-vibe-ai-coding-frameworks](https://dzone.com/articles/beyond-vibe-ai-coding-frameworks)  
10. What is BMAD-METHOD™? A Simple Guide to the Future of AI-Driven Development, consulté le février 2, 2026, [https://medium.com/@visrow/what-is-bmad-method-a-simple-guide-to-the-future-of-ai-driven-development-412274f91419](https://medium.com/@visrow/what-is-bmad-method-a-simple-guide-to-the-future-of-ai-driven-development-412274f91419)  
11. BMAD: AI-Powered Agile Framework Overview | by Plaban Nayak | Dec, 2025 \- Medium, consulté le février 2, 2026, [https://nayakpplaban.medium.com/bmad-ai-powered-agile-framework-overview-238d4af39aa4](https://nayakpplaban.medium.com/bmad-ai-powered-agile-framework-overview-238d4af39aa4)  
12. BMAD-METHOD \- Universal AI Agent Framework Tutorial Guide, consulté le février 2, 2026, [https://bmadmethodguide.com/](https://bmadmethodguide.com/)  
13. 23 Best AI Coding Tools for Developers Heading Into 2026 \- Jellyfish, consulté le février 2, 2026, [https://jellyfish.co/blog/best-ai-coding-tools/](https://jellyfish.co/blog/best-ai-coding-tools/)  
14. 15 Best AI Tools for Developers in 2026 \[Free and Paid\] \- Openxcell, consulté le février 2, 2026, [https://www.openxcell.com/blog/ai-tools-for-developers/](https://www.openxcell.com/blog/ai-tools-for-developers/)  
15. Best AI Coding Tools for Developers in 2026 \- Builder.io, consulté le février 2, 2026, [https://www.builder.io/blog/best-ai-tools-2026](https://www.builder.io/blog/best-ai-tools-2026)  
16. How to Supercharge Your AI Coding Workflow with MCP (Model Context Protocol), consulté le février 2, 2026, [https://www.codingmoney.com/blog/how-to-supercharge-your-ai-coding-workflow-with-mcp-model-context-protocol/](https://www.codingmoney.com/blog/how-to-supercharge-your-ai-coding-workflow-with-mcp-model-context-protocol/)  
17. MCP Directory | Cursor Docs, consulté le février 2, 2026, [https://cursor.com/docs/context/mcp/directory](https://cursor.com/docs/context/mcp/directory)  
18. Web Development | Cursor Docs, consulté le février 2, 2026, [https://cursor.com/docs/cookbook/web-development](https://cursor.com/docs/cookbook/web-development)  
19. Cursor MCP — A 5-Minute Quick Start Guide | by Yehuda Levi | Medium, consulté le février 2, 2026, [https://medium.com/@levi\_yehuda/cursor-mcp-a-5-minute-quick-start-guide-3c6f214557d5](https://medium.com/@levi_yehuda/cursor-mcp-a-5-minute-quick-start-guide-3c6f214557d5)  
20. ochapple/chrome-devtools-mcp-cursor-guide: Chrome ... \- GitHub, consulté le février 2, 2026, [https://github.com/ochapple/chrome-devtools-mcp-cursor-guide](https://github.com/ochapple/chrome-devtools-mcp-cursor-guide)  
21. ChromeDevTools/chrome-devtools-mcp: Chrome DevTools ... \- GitHub, consulté le février 2, 2026, [https://github.com/ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp)  
22. Chrome DevTools MCP × Cursor IDE — Guide & Starter \- LobeHub, consulté le février 2, 2026, [https://lobehub.com/mcp/ochapple-chrome-devtools-mcp-cursor-guide](https://lobehub.com/mcp/ochapple-chrome-devtools-mcp-cursor-guide)  
23. Browser | Cursor Docs, consulté le février 2, 2026, [https://cursor.com/docs/agent/browser](https://cursor.com/docs/agent/browser)  
24. Rapid Prototyping with Cursor | Cursor Docs, consulté le février 2, 2026, [https://cursor.com/for/prototyping](https://cursor.com/for/prototyping)  
25. What Is Threat Hunting? \- Palo Alto Networks, consulté le février 2, 2026, [https://www.paloaltonetworks.com/cyberpedia/threat-hunting](https://www.paloaltonetworks.com/cyberpedia/threat-hunting)  
26. Threat Hunting Explained: Process, Tools and Benefits | Okta, consulté le février 2, 2026, [https://www.okta.com/identity-101/threat-hunting/](https://www.okta.com/identity-101/threat-hunting/)  
27. What Is Cyber Threat Hunting? Definition, Examples and Useful Tools, consulté le février 2, 2026, [https://www.cm-alliance.com/cybersecurity-blog/what-is-cyber-threat-hunting-definition-examples-and-useful-tools](https://www.cm-alliance.com/cybersecurity-blog/what-is-cyber-threat-hunting-definition-examples-and-useful-tools)  
28. Better AI Driven Development with Test Driven Development | by Eric Elliott \- Medium, consulté le février 2, 2026, [https://medium.com/effortless-programming/better-ai-driven-development-with-test-driven-development-d4849f67e339](https://medium.com/effortless-programming/better-ai-driven-development-with-test-driven-development-d4849f67e339)  
29. The creator of Claude Code's Claude setup | Hacker News, consulté le février 2, 2026, [https://news.ycombinator.com/item?id=46470017](https://news.ycombinator.com/item?id=46470017)  
30. This is interesting to hear, but I don't understand how this workflow actually w... | Hacker News, consulté le février 2, 2026, [https://news.ycombinator.com/item?id=46523312](https://news.ycombinator.com/item?id=46523312)  
31. Leveraging Test-Driven Development (TDD) for AI System Architecture | Galileo, consulté le février 2, 2026, [https://galileo.ai/blog/tdd-ai-system-architecture](https://galileo.ai/blog/tdd-ai-system-architecture)  
32. Top AI Tools for Developers to Build Faster and Smarter in 2026, consulté le février 2, 2026, [https://www.builtthisweek.com/blog/top-ai-tools-for-developers-2026](https://www.builtthisweek.com/blog/top-ai-tools-for-developers-2026)  
33. AI Literacy Storage | Atale Group, consulté le février 2, 2026, [https://www.atalegroup.com/ai-literacy-storage](https://www.atalegroup.com/ai-literacy-storage)  
34. J'aimerais demander à tout le monde son expérience avec BMAD-METHOD dans Claude Code \- Reddit, consulté le février 2, 2026, [https://www.reddit.com/r/ClaudeAI/comments/1mmn41s/i\_would\_like\_to\_ask\_everyone\_about\_claude\_codes/?tl=fr](https://www.reddit.com/r/ClaudeAI/comments/1mmn41s/i_would_like_to_ask_everyone_about_claude_codes/?tl=fr)  
35. Quelqu'un ici utilise sérieusement la méthode BMAD pour le vibe coding ? Ça vaut le coup ou c'est du délire ? : r/vibecoding \- Reddit, consulté le février 2, 2026, [https://www.reddit.com/r/vibecoding/comments/1m3b02m/anyone\_here\_seriously\_using\_the\_bmad\_method\_for/?tl=fr](https://www.reddit.com/r/vibecoding/comments/1m3b02m/anyone_here_seriously_using_the_bmad_method_for/?tl=fr)  
36. 12 Best AI Agent Frameworks in 2026 | Data Science Collective \- Medium, consulté le février 2, 2026, [https://medium.com/data-science-collective/the-best-ai-agent-frameworks-for-2026-tier-list-b3a4362fac0d](https://medium.com/data-science-collective/the-best-ai-agent-frameworks-for-2026-tier-list-b3a4362fac0d)  
37. 10 Best Software Development Methodologies for 2026 \- Relinns Technologies, consulté le février 2, 2026, [https://relinns.com/blogs/best-software-development-methodologies](https://relinns.com/blogs/best-software-development-methodologies)  
38. Generating Your First Rules with Cursor for Your Angular Project \- DEV Community, consulté le février 2, 2026, [https://dev.to/alfredoperez/generating-your-first-rules-with-cursor-for-your-angular-project-490k](https://dev.to/alfredoperez/generating-your-first-rules-with-cursor-for-your-angular-project-490k)  
39. BMad's Best Practices Cursor Custom Agents and Rules Generator \- GitHub Gist, consulté le février 2, 2026, [https://gist.github.com/bossjones/1fd99aea0e46d427f671f853900a0f2a](https://gist.github.com/bossjones/1fd99aea0e46d427f671f853900a0f2a)  
40. Ultimate Rule Generator \- No more failure to generate and Private Rules\! \- Built for Cursor, consulté le février 2, 2026, [https://forum.cursor.com/t/ultimate-rule-generator-no-more-failure-to-generate-and-private-rules/51782](https://forum.cursor.com/t/ultimate-rule-generator-no-more-failure-to-generate-and-private-rules/51782)  
41. Cursor Auto Rule Generation that Actually Works and Produces highly optimized rules that will get picked up at the right time by the Composer\! Solves the fail to create rules files issue also\! \- Reddit, consulté le février 2, 2026, [https://www.reddit.com/r/cursor/comments/1is4fzr/cursor\_auto\_rule\_generation\_that\_actually\_works/](https://www.reddit.com/r/cursor/comments/1is4fzr/cursor_auto_rule_generation_that_actually_works/)  
42. rosendolu/cursor-rules-deploy: CLI tool for deploying Cursor AI rules and templates \- GitHub, consulté le février 2, 2026, [https://github.com/rosendolu/cursor-rules-deploy](https://github.com/rosendolu/cursor-rules-deploy)  
43. Top Solo Developer AI Tools to Ship Products Faster in 2026 \- Built This Week, consulté le février 2, 2026, [https://www.builtthisweek.com/blog/solo-developer-ai-tools](https://www.builtthisweek.com/blog/solo-developer-ai-tools)