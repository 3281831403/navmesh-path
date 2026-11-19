# 导航网格寻路：启发式、代价与动态障碍

守卫在拐角处卡住：启发式与真实代价不一致，对角线代价按直线算，动态障碍没有让缓存失效，路径没有视线平滑，人群分离力叠加爆掉，分层网格坐标映射错，代价没钳制，异步结果过期仍被采用，缓存键漏了版本，批量 agent 只提交一半。

## 目录结构

```
README.md
conftest.py
.gitignore
gameplay/__init__.py
gameplay/navmesh.py
tests/test_navmesh.py
```

## 当前状态

`gameplay/navmesh.py` 中所有函数只保留签名与文档字符串，函数体统一
`raise NotImplementedError`。`tests/test_navmesh.py` 有 15 个参数化用例，
初始全部失败。

## 需要修复的 10 个问题

1. 启发式与真实代价一致
2. 对角线代价按 √2 计算
3. 动态障碍使缓存失效
4. 路径按视线平滑
5. 人群分离力按半径叠加
6. 分层网格坐标映射
7. 单步代价钳制
8. 过期异步结果丢弃
9. 缓存键包含版本
10. 批量 agent 统一提交

## 验收

```bash
python -m pytest -q
```

初始应得到 `15 failed`，且没有 collection error。实现 `gameplay/navmesh.py`
后 15 条用例应全部通过。
