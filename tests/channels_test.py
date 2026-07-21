from velbusaio.channels import Channel


def test_channel_set_name_char():
    channel = Channel(None, None, "placeholder", False, False, None, None)
    name = "FooBar"
    for pos in range(16):
        ch = ord(name[pos]) if pos < len(name) else 0xFF
        channel.set_name_char(pos, ch)
    assert channel.get_name() == "FooBar\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
