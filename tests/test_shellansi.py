#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
from i3pystatus.shell_ansi import AnsiShell


class DummyModule(AnsiShell):
    """
    Subclass for testing: overrides `run` to capture output instead of i3pystatus display.
    """
    def __init__(self, command, **kwargs):
        self.command = command
        self.interval = kwargs.get("interval", 5)
        self.ansi_color_map = kwargs.get("ansi_color_map", None)
        self.default_color = kwargs.get("default_color", "#FFFFFF")
        self.hide_if_empty = kwargs.get("hide_if_empty", False)
        self.output = None

    def run_module(self):
        self.run()
        return self.output


def test_basic_colors():
    command = "echo -e '\033[31mRED_TEXT\033[0m'"
    module = DummyModule(command)
    out = module.run_module()
    # full_text stripped of ANSI
    assert out["full_text"] == "RED_TEXT"
    # color from default ANSI map (or Xresources if loaded)
    assert out["color"].startswith("#") and len(out["color"]) == 7
    print("test_basic_colors passed")


def test_empty_output():
    command = "echo -n ''"
    module = DummyModule(command, hide_if_empty=True)
    out = module.run_module()
    # full_text should be empty string
    assert out["full_text"] == ""
    assert out["color"] == module.default_color
    print("test_empty_output passed")


def test_manual_override():
    command = "echo -e '\033[32mGREEN_TEXT\033[0m'"
    module = DummyModule(command, ansi_color_map={'32': '#00AA00'}, default_color="#AAAAAA")
    out = module.run_module()
    assert out["full_text"] == "GREEN_TEXT"
    assert out["color"] == "#00AA00"
    print("test_manual_override passed")


if __name__ == "__main__":
    test_basic_colors()
    test_empty_output()
    test_manual_override()
    print("All tests passed!")
