// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - demo: 用对称 API 跑通最小可运行闭环
// 对照 Python README:
//   app = App(); setSkin(Skin.NEOBRUTALISM)
//   w = app.create_window(WindowType.BAR); w.setWindowTitle("..."); w.resize(...); w.show()
#include "prism/App.h"
#include "prism/Theme.h"

#include <QDebug>

int main(int argc, char *argv[]) {
    using namespace prism;

    App app(argc, argv);

    // 一行切换设计语言 (镜像 Python setSkin(Skin.NEOBRUTALISM))
    setSkin(Skin::Fluent);
    setAccentColor("#F97316");   // PrismQML 招牌橙, 验证主题色流过 Enums

    qInfo() << "skin =" << skinToString(getSkin())
            << "accent =" << getAccentColor() << "isDark =" << isDark();

    Window &w = app.createWindow(WindowType::Bar);
    w.setWindowTitle(QStringLiteral("PrismQML C++ 宿主 Demo"));
    w.resize(1200, 800);

    if (!w.isValid()) {
        qCritical() << "DEMO_FAIL: 窗口创建失败";
        return 2;
    }
    qInfo() << "DEMO_OK: prism::Window created via C++ host";

    w.show();
    return app.exec();
}
