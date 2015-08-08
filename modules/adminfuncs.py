# autorejoin
# delayed rejoin on kick
from twisted.internet import reactor
from util import Mapping, commandSplit
from util.irctools import escape_control_codes as esc, AAA

CHANNEL_PREFIXES = '&#!+'


def admin_join(event, bot):
	channel, key = commandSplit(event.argument)

	if not channel:
		return bot.say(".%s #channel [key]" % event.command)
	elif channel[0] not in CHANNEL_PREFIXES:
		channel = '#' + channel

	if key:
		reactor.callFromThread(bot.join, channel, key)
		return bot.say("Attempting to join (%s) with key (%s)." % (channel, key))
	else:
		reactor.callFromThread(bot.join, channel)
		return bot.say("Attempting to join (%s)." % channel)


def admin_part(event, bot):
	channel, reason = commandSplit(event.argument)

	if not channel:
		bot.say("Bye.")
		return reactor.callFromThread(bot.leave, event.target)
	elif channel[0] not in CHANNEL_PREFIXES:
		channel = '#' + channel

	if reason:
		reactor.callFromThread(bot.leave, channel, reason)
		return bot.say("Attempting to part (%s) with reason (%s)." % (channel, reason))
	else:
		reactor.callFromThread(bot.leave, channel)
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
			reactor.callFromThread(bot.sendmsg, chan_or_user, msg)
			return bot.say("Attempted to send message (%s) to (%s)." % (esc(msg), chan_or_user))
	elif not msg:
		return bot.say(".%s message" % event.command)

	reactor.callFromThread(bot.sendmsg, event.target, msg)


def admin_action(event, bot):
	msg = event.argument

	if event.isPM():
		chan_or_user, msg = commandSplit(msg)
		if not chan_or_user or not msg:
			return bot.say(".%s #channel action" % event.command)
		else:
			reactor.callFromThread(bot.sendmsg, chan_or_user, "\x01ACTION %s\x01" % msg)
			return bot.say("Attempted to send action (%s) to (%s)." % (esc(msg), chan_or_user))
	elif not msg:
		return bot.say(".%s action" % event.command)

	reactor.callFromThread(bot.sendmsg, event.target, "\x01ACTION %s\x01" % msg)


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
			reactor.callFromThread(bot.sendmsg, chan_or_user, msg)
			return bot.say("Attempted to send furious message (%s) to (%s)." % (esc(msg), chan_or_user))

	reactor.callFromThread(bot.sendmsg, event.target, AAA(msg))


mappings = (Mapping(command="join", function=admin_join, admin=True),
			Mapping(command="part", function=admin_part, admin=True),
			Mapping(command="kick", function=admin_kick, admin=True),
			Mapping(command=("msg", "message", "pm"), function=admin_msg, admin=True),
			Mapping(command=("action", "me"), function=admin_action, admin=True),
			Mapping(command=("rage", "fury"), function=admin_rage, admin=True))
