# AGNES Media Generation Skill

通过 [AGNES AI](https://www.agnes-ai.cn) API 生成图片和视频的 WorkBuddy / Claude Code / Cursor 技能包。

## 支持的模型

| 类型 | 模型 ID | 价格 |
|------|---------|------|
| 图片生成 | `agnes-image-2.5-flash` | 免费 |
| 视频生成 | `agnes-video-v2.0` | 免费 |

## 安装方法

### 方式一：通过 GitHub（推荐）

在你的智能体（WorkBuddy / Claude Code / Cursor）中说：

> 帮我安装这个 Skill：https://github.com/IvanXxxxyyuffff/agnes-media-generation

### 方式二：手动安装

1. 下载或克隆本仓库
2. 将整个文件夹复制到 skills 目录：
   - WorkBuddy: `~/.workbuddy/skills/agnes-media-generation/`
   - Claude Code: `~/.claude/skills/agnes-media-generation/`
   - Cursor: `~/.cursor/skills/agnes-media-generation/`
3. 重启你的智能体

## 配置 API Key

首次使用时，Skill 会提示你填入 API Key：

1. 打开 https://www.agnes-ai.cn 免费注册
2. 在 API Key 管理页面创建一个 Key（以 `sk-` 开头）
3. 把 Key 填入 `scripts/.env` 文件：
   ```
   AGNES_API_KEY=sk-你的key
   ```

> API Key 仅保存在你本地，不会上传到任何服务器。

## 使用示例

- 「生成一张赛博朋克城市的图片」
- 「生成一个猫咪在沙滩散步的视频」

## 命令行用法

```bash
# 安装依赖
pip install -r requirements.txt

# 生成图片
python scripts/agnes_media.py image "夕阳下的雪山"

# 生成视频
python scripts/agnes_media.py video "赛博朋克城市夜景"
```

## 已知限制

- 视频接口不接受 `width`/`height` 参数，传了会报 forbidden field
- 免费用户视频生成有频率限制，频繁调用会返回 429

## License

MIT
