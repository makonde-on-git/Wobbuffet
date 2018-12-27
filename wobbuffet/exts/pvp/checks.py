async def is_proper_channel(ctx, expected_channel):
    if not expected_channel or expected_channel == 0:
        return True
    if type(expected_channel) is not list:
        expected_channel = [expected_channel]
    return ctx.channel.id in expected_channel
