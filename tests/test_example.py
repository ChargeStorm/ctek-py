from ctek.nanogrid_air import NanogridAir


def test_nanogrid_air_print(capsys):
    NanogridAir().print()
    captured = capsys.readouterr()
    assert captured.out == "Hello from NANOGRID™ AIR\n"
