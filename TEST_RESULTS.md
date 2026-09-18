# 测试记录

- 最近复测日期：2026-09-18
- Python：3.13.0
- 命令：`python -m unittest discover -s tests -v`
- 结果：12 项全部通过，耗时 23.957 秒

```text
test_t01_unblocked_arrow_disappears ... ok
test_t02_blocked_arrow_stays_and_costs_a_miss ... ok
test_t03_boundary_arrow_exits_normally ... ok
test_t04_clear_level_and_enter_next ... ok
test_t05_misses_exhausted_causes_game_over ... ok
test_t06_restart_restores_arrows_and_misses ... ok
test_hint_returns_an_unblocked_arrow ... ok
test_undo_restores_arrow_misses_and_score ... ok
test_level_selection_loads_requested_level ... ok
test_all_levels_are_valid_and_solvable ... ok
test_progress_can_be_saved_and_loaded ... ok
test_broken_progress_file_is_safe ... ok

Ran 12 tests in 23.957s
OK
```

此外，已在 Windows 桌面实际启动 Tkinter 程序，并检查开始界面、第一关游戏界面和过关界面；对应截图位于 `screenshots/`。

GUI 动画专项冒烟测试：在加入提示、撤销、计时、积分、星级和关卡选择后，先自动点击第一关被阻挡的向右飞剑，确认飞剑回弹后仍在原位、剑心由 3 减为 2；再点击无阻挡飞剑，确认它加速飞出棋盘并从状态中消失。图片飞剑版已在 Windows 桌面实际启动并完成视觉检查。测试输出：

```text
GUI smoke test OK: collision, flight, score, undo and hint all finished
```
