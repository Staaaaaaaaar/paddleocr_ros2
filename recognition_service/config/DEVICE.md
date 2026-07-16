# 适用设备信息（占位，部署前请填写）

| 项目 | 值 |
|------|-----|
| 设备名称 | `<DEVICE_NAME>` |
| 设备型号 | `<MODEL_NAME>` |
| 生产厂商 | `<MANUFACTURER>` |
| 屏幕规格 | `<SCREEN_WIDTH>` × `<SCREEN_HEIGHT>` |
| 固件版本 | `<FIRMWARE_VERSION>` |
| 备注 | `<NOTES>` |

本目录（`recognition_service/config/`）与 `assets/digit_templates/` 中的标定数据仅对上述型号有效。

更换设备后请：

1. 更新本文件
2. 重新标定 `rois.json`、`compass.json`、`digit_slots.json`
3. 删除 `assets/digit_templates/` 并重新运行识别以生成模板
4. 重启识别 HTTP 服务
