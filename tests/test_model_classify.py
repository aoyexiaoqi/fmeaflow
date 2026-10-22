from fmeaflow.checks import has_sc_marking
from fmeaflow.classify import classify_control, controls_match, split_controls
from fmeaflow.model import norm_step_no, norm_text, step_key


def test_norm_text_strips_and_lowers():
    assert norm_text("  Ab C ") == "abc"
    assert norm_text("首 件　检验") == "首件检验"
    assert norm_text(None) == ""


def test_norm_step_no():
    assert norm_step_no("010") == "10"
    assert norm_step_no(10.0) == "10"
    assert norm_step_no("10.0") == "10"
    assert norm_step_no(" OP-5 ") == "op-5"
    assert step_key("010", "上 料") == ("10", "上料")


def test_classify_explicit_type_wins():
    assert classify_control("随便什么", "预防") == "prevention"
    assert classify_control("随便什么", "探测") == "detection"


def test_classify_keywords():
    assert classify_control("防错定位销") == "prevention"
    assert classify_control("压力传感器联锁") == "prevention"
    assert classify_control("首件检验") == "detection"
    assert classify_control("X光抽检") == "detection"
    assert classify_control("") == "unknown"
    assert classify_control("其他") == "unknown"


def test_split_and_match_controls():
    assert split_controls("首件检验；全检目视、抽检") == ["首件检验", "全检目视", "抽检"]
    assert split_controls("") == []
    assert controls_match("首件检验", "首件检验（每班）")
    assert controls_match("在线压力监测", "在线压力监测")
    assert not controls_match("防错定位销", "首件检验")


def test_sc_marking():
    assert has_sc_marking("CC")
    assert has_sc_marking("◆")
    assert has_sc_marking("重要特性")
    assert not has_sc_marking("")
    assert not has_sc_marking("无")
