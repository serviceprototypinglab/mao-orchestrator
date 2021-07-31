# MAO Installer and Marketplace

For a more continent user experience during federation setup or joining of a new MAO instance the framework offers an installer that guides users trough the setup process of a new instance as well as there optional join with an existing federation.

The discovery mechanism for federations, pipelines and tools is baked by the MAO marketplace that acts as a global hub for information exchange between MAO federations and users.

## MAO Marketplace

The first version of the marketplace consists of the plain JSON files that are update by the MAO core team.

The base URL for the marketplace is `https://mao-mao-research.github.io/hub/api/<component>.json` followed by a specific component JSON file:

- `federations.json` - Overs an overview about existing MAO federations as well as basic contact information if a user whats to join
- `tools.json` - Overs a collection of curated tools that can be used in MAO pipelines
- `pipelines.json` - Overs a collection of curated pipelines that mostly are able to run out of the box and produce sensible metrics right away

## MAO Installer

The information available on the MAO marketplace is used by the MAO installer to enhance the installation and initialization procedure of a new MAO instance.

To run the installer a user can use the `instance` subcommands provided by the `maoctl.py`. Details about the setup process can be found in the projects main README which can be found [here](../README.md).

Installer process overview:
1. `instance install` - installs a new MAO instance on the system executed (interactively gathering necessary information from the user)
2. `instance init` - initializes a new or existing MAO instance. This command can be executed multiple times and allows the user to register new tools and pipelines from the MAO marketplace.