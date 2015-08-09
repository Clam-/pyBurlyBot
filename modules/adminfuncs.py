from util import Mapping, commandSplit, TimeoutException
from util.irctools import escape_control_codes as esc, AAA
from twisted.words.protocols.irc import CHANNEL_PREFIXES


JOIN_TIMEOUT = 10
# https://tools.ietf.org/html/rfc1459#page-20
ERR_NOSUCHCHANNEL   = '403'
ERR_TOOMANYCHANNELS = '405'
ERR_NEEDMOREPARAMS  = '461'
ERR_CHANNELISFULL   = '471'
ERR_INVITEONLYCHAN  = '473'
ERR_BANNEDFROMCHAN  = '474'
ERR_BADCHANNELKEY   = '475'
ERR_BADCHANMASK     = '476'


def admin_join(event, bot):
	channel, key = commandSplit(event.argument)

	if not channel:
		return bot.say(".%s #channel [key]" % event.command)
	elif channel[0] not in CHANNEL_PREFIXES:
		channel = '#' + channel

	bot.join(channel, key)
	try:
		for event in bot.send_and_wait(None, stope=("joined", ERR_BADCHANNELKEY, ERR_BANNEDFROMCHAN,
													ERR_INVITEONLYCHAN, ERR_BADCHANMASK, ERR_CHANNELISFULL,
													ERR_TOOMANYCHANNELS, ERR_NOSUCHCHANNEL),
						f=bot.join, fargs=(channel, key), timeout=JOIN_TIMEOUT):
			if event.type == ERR_BADCHANNELKEY and event.params[1] == channel:
				bot.say("Failed to join (%s), incorrect key (received ERR_BADCHANNELKEY)." % channel)
				break
			elif event.type == ERR_TOOMANYCHANNELS and event.params[1] == channel:
				bot.say("Failed to join (%s), we've joined too many channels (received ERR_TOOMANYCHANNELS)." % channel)
				break
			elif event.type == ERR_NOSUCHCHANNEL and event.params[1] == channel:
				bot.say("Failed to join (%s), no such channel (received ERR_NOSUCHCHANNEL)." % channel)
				break
			elif event.type == ERR_INVITEONLYCHAN and event.params[1] == channel:
				bot.say("Failed to join (%s), invite only (received ERR_INVITEONLYCHAN)." % channel)
				break
			elif event.type == ERR_CHANNELISFULL and event.params[1] == channel:
				bot.say("Failed to join (%s), channel is full (received ERR_CHANNELISFULL)." % channel)
				break
			elif event.type == ERR_BADCHANMASK and event.params[1] == channel:
				bot.say("Failed to join (%s), received ERR_BADCHANMASK." % channel)
				break
			elif event.type == ERR_NEEDMOREPARAMS and event.params[1] == channel:
				bot.say("Failed to join (%s), received ERR_NEEDMOREPARAMS." % channel)
				break
			elif event.type == "joined" and event.target == channel:
				r_msg = "Successfully joined (%s)" % channel
				if key:
					r_msg += " with key (%s)" % key
				bot.say(r_msg + '.')
				break
			print event.params
	except TimeoutException:
		bot.say("Failed to join (%s) in (%d second) timeout." % (channel, JOIN_TIMEOUT))


def admin_part(event, bot):
	channel, reason = commandSplit(event.argument)

	if not channel:
		bot.say("Bye.")
		return bot.leave(event.target)
	elif channel[0] not in CHANNEL_PREFIXES:
		channel = '#' + channel

	if reason:
		bot.leave(channel, reason)
		return bot.say("Attempting to part (%s) with reason (%s)." % (channel, reason))
	else:
		bot.leave(channel)
		return bot.say("Attempting to part (%s)." % channel)


def admin_kick(event, bot):
	channel, user = commandSplit(event.argument)
	user, reason = commandSplit(user)

	if not channel or not user:
		return bot.say(".%s #channel user [reason]" % event.command)
	elif channel[0] not in CHANNEL_PREFIXES:
		channel = '#' + channel

	if reason:
		bot.say("Attempting to kick (%s) from (%s) with reason (%s)." % (user, channel, reason))
		return bot.kick(channel, user, reason)
	else:
		bot.say("Attempting to kick (%s) from (%s)." % (user, channel))
		return bot.kick(channel, user)


def admin_msg(event, bot):
	msg = event.argument

	if event.isPM():
		chan_or_user, msg = commandSplit(msg)
		if not chan_or_user or not msg:
			return bot.say(".%s #channel message" % event.command)
		else:
			bot.sendmsg(chan_or_user, msg)
			return bot.say("Attempted to send message (%s) to (%s)." % (esc(msg), chan_or_user))
	elif not msg:
		return bot.say(".%s message" % event.command)

	bot.sendmsg(event.target, msg)


def admin_action(event, bot):
	msg = event.argument

	if event.isPM():
		chan_or_user, msg = commandSplit(msg)
		if not chan_or_user or not msg:
			return bot.say(".%s #channel action" % event.command)
		else:
			bot.sendmsg(chan_or_user, "\x01ACTION %s\x01" % msg)
			return bot.say("Attempted to send action (%s) to (%s)." % (esc(msg), chan_or_user))
	elif not msg:
		return bot.say(".%s action" % event.command)

	bot.sendmsg(event.target, "\x01ACTION %s\x01" % msg)


def admin_rage(event, bot):
	msg = event.argument

	if not msg:
		from random import randint
		msg = 'A' * randint(200, 400)

	if event.isPM():
		chan_or_user, msg = commandSplit(msg)
		if not chan_or_user or not msg:
			return bot.say(".%s #channel furious_message" % event.command)
		else:
			msg = AAA(msg)
			bot.sendmsg(chan_or_user, msg)
			return bot.say("Attempted to send furious message (%s) to (%s)." % (esc(msg), chan_or_user))

	bot.sendmsg(event.target, AAA(msg))


mappings = (Mapping(command="join", function=admin_join, admin=True),
			Mapping(command="part", function=admin_part, admin=True),
			Mapping(command="kick", function=admin_kick, admin=True),
			Mapping(command=("msg", "message", "say", "pm"), function=admin_msg, admin=True),
			Mapping(command=("action", "me"), function=admin_action, admin=True),
			Mapping(command=("rage", "fury"), function=admin_rage, admin=True))
