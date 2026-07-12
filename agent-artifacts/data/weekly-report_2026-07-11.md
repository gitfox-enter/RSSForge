# RSSForge 周报 - 2026-07-11

## 任务执行情况

### ✅ 正常运行（count > 0）
- **线报酷**: 7609 条（高频更新）
- **线报ICU**: 1013 条
- **汇发部**: 7376 条（高频更新）
- **专业线报**: 314 条
- **线报网**: 89 条
- **超级线报**: 191 条
- **爱Q社区**: 157 条
- **牙线之**: 94 条
- **风行影用**: 31 条
- **网侯线报**: 20 条
- **有法恩图**: 95 条
- **专栏吧**: 524 条

**总计：12 个站点正常运行**

---

### 🔧 疑似失效（count = 0）

#### 高频站点（interval ≤ 30min）
1. **线报迷** - https://xianbaomi.com/
2. **小角落** - https://yangmao.19970709.xyz/
3. **ReadHub 热门** - https://readhub.cn/hot
4. **新赚吧** - https://xzba.cc/
5. **H6线报** - https://www.h6room.com/
6. **羊毛王** - https://yangmao.wang/
7. **羊毛党** - https://www.yangmaodang.club/
8. **羊毛线报** - https://b1.ymxianbao.cn/
9. **007羊毛党** - https://www.007ymd.com/
10. **12345线报** - https://www.12345pro.com/
11. **天天赚钱** - https://www.daydayzhuan.com/
12. **网赚** - https://www.wycad.com/
13. **羊毛群** - https://blog.xianbao.art/

#### 中频站点（interval 60-120min）
14. **好赚网** - https://m.hybase.com/
15. **活动5** - https://www.huodong5.com/
16. **我不是人** - https://www.wobangzhao.com/
17. **白菜哦** - https://www.baicaio.com/
18. **吧操哦** - https://www.bacaoo.com/
19. **优选惠线报** - https://www.yxssp.com/
20. **都市线报族** - https://www.douban.com/group/711811/
21. **开心赚** - https://www.kxdao.net/forum-42-1.html
22. **51看看** - https://www.51kanong.com/
23. **IT之家** - https://www.ithome.com/zt/xijiaiyi

#### 低频站点（interval ≥ 240min）
24. **喵喵猫** - https://www.manmanbuy.com/
25. **全国各报可看** - https://www.ghxi.com/
26. **423Down** - https://www.423down.com/
27. **八仙过海情报局** - https://www.appinn.com/
28. **LSapk** - https://www.lsapk.com/
29. **迈丰首页** - https://www.thosefree.com/
30. **分享软件** - https://www.foxirj.com/
31. **梵多下载面** - https://free.apprcn.com/
32. **异次元RSS** - https://feed.iplaysoft.com/
33. **试玩云集** - https://10000yun.com/
34. **APP喵** - https://www.appmiu.com/
35. **优惠券情报局** - https://yrxq.xianggexi.vip/
36. **线报乌** - https://www.hxm5.com/

**总计：36 个站点疑似失效（count = 0）**

---

## 分析结论

### 健康度
- **健康站点**: 12/48 (25%)
- **疑似失效**: 36/48 (75%)

### 高频站点失效严重
- 线报类站点失效比例极高（线报迷、小角落、羊毛系列等）
- 这些站点抓取间隔 20-30 分钟，长期 count=0 说明源站可能：
  - 域名失效
  - 反爬升级
  - 内容停止更新
  - 解析器失效

### 建议行动
1. **抽查测试**：手动访问 10 个失效站点的 `site_url`，确认是否可访问
2. **解析器检查**：检查 sites.yaml 中对应的 parser 配置
3. **清理或修复**：
   - 确认失效的从 sites.yaml 移除
   - 可访问但解析失败的修复 parser

---

## 网络问题
由于沙箱网络不稳定（Git clone 失败、GitHub API 超时），本次分析基于已有的 feeds_meta.json 数据，未能实时验证 feed 状态。建议在网络稳定时重新检查。

---

## 下一步
- 等待网络稳定后执行实时检查
- 或者在本地环境执行 git pull + feed 测试
