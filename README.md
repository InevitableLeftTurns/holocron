# Holocron Discord Bot
Discord Bot for Star Wars: Galaxy of Heroes Hint Tracking

Holocron is a Discord bot for collecting and remembering Tips for the Star Wars Galaxy of Heroes game. Created for the guild: Mando's Mudhorns. The actual code repo is public for the time being but privately managed.

The Holocron bot allows members to add Tips for battles and the guild can look up those tips in the bot channel.

### Supported Holocrons
* Conquest
* Rise of the Empire
* Territory War and GAC Counters

Given Discord's interface of messages and emojis, the bot relies on an address supported for each Holocron and text commands. This repo is specifically for comments, requests, and bug reports.

For basic usage try `.help`
  List of Holocrons and Commands.
  For detailed help, use .help [holocron|command]
  
### Holocrons
  * .conquest (aliases: c, con, conq) - Access the Conquest Holocron for reading and managing Conquest Tips
  * .rise (aliases: r) - Access the Rise Holocron for reading and managing Rise Tips
  * .war (aliases: tw, gac, counter) - Access the War Holocron for reading and managing Territory War and Grand Arena Championship Counter Tips
  
### Commands
  * .help (aliases: h) - Provides help on Holocron and admin commands.
  * .settings (aliases: none) - A list of server settings which can be changed (requires admin)



Each Holocron also has its own help using `.<holocron> help`. ex: `.con help`
