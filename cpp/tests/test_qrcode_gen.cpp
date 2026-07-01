// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - QRCodeGenerator 端到端验证: 真实生成 QR PNG 供解码器还原比对。
// 生成一组不同内容/尺寸/纠错级的二维码, 落盘 PNG + 清单 manifest.tsv,
// 由 tests/qr/verify_qr.py 用 opencv 解码, 断言解出内容 == 原文。
#include "prism/QRCodeGenerator.h"
#include "prism/Accessors.h"

#include <QGuiApplication>
#include <QDebug>
#include <QDir>
#include <QFile>
#include <QImage>
#include <QSize>
#include <QTextStream>

using namespace prism;

int main(int argc, char *argv[]) {
    QGuiApplication app(argc, argv);

    // 输出目录: 命令行参数 argv[1], 否则临时目录
    QString outDir = (argc > 1) ? QString::fromLocal8Bit(argv[1])
                                : QDir::temp().filePath(QStringLiteral("prism_qr_verify"));
    QDir().mkpath(outDir);

    // available() 必须为 true (编码后端已接入)
    if (!QRCodeGenerator::instance()->available()) {
        qCritical() << "FAIL: QRCodeGenerator.available() == false";
        return 2;
    }

    // 测试用例: 内容 / 尺寸 / 纠错级 (含 URL / 中文 / 长文本 / 特殊符号)
    struct Case { QString content; int size; QString level; };
    const QList<Case> cases = {
        {QStringLiteral("https://github.com/aki-riko/PrismQML"), 300, QStringLiteral("M")},
        {QStringLiteral("Hello, PrismQML C++ host!"), 200, QStringLiteral("L")},
        {QStringLiteral("二维码中文内容测试 PrismQML"), 360, QStringLiteral("Q")},
        {QStringLiteral("1234567890-=[]\\;',./`~!@#$%^&*()"), 250, QStringLiteral("H")},
        {QStringLiteral("The quick brown fox jumps over the lazy dog. "
                        "0123456789. PrismQML end-to-end QR verification."), 400,
         QStringLiteral("M")},
    };

    QRCodeImageProvider provider;
    QFile manifest(QDir(outDir).filePath(QStringLiteral("manifest.tsv")));
    if (!manifest.open(QIODevice::WriteOnly | QIODevice::Text)) {
        qCritical() << "FAIL: 无法写 manifest";
        return 3;
    }
    QTextStream ts(&manifest);
    ts.setEncoding(QStringConverter::Utf8);

    int idx = 0;
    for (const Case &c : cases) {
        // 走 getImageSource 生成规范 id, 再交 provider (端到端路径, 与 QML 一致)
        const QString url = QRCodeGenerator::instance()->getImageSource(
            c.content, c.size, QStringLiteral("#000000"), QStringLiteral("#ffffff"), c.level);
        // url = image://qrcode/<id>, 取 id 部分喂 provider
        const QString id = url.mid(QStringLiteral("image://qrcode/").size());

        QSize realSize;
        QImage img = provider.requestImage(id, &realSize, QSize());
        if (img.isNull()) {
            qCritical() << "FAIL: 生成空图" << c.content;
            return 4;
        }
        const QString png = QDir(outDir).filePath(QStringLiteral("qr_%1.png").arg(idx));
        if (!img.save(png, "PNG")) {
            qCritical() << "FAIL: 保存 PNG 失败" << png;
            return 5;
        }
        // manifest 一行: 文件名 \t 原文 (原文里的 \t/\n 不出现在用例中)
        ts << QStringLiteral("qr_%1.png").arg(idx) << '\t' << c.content << '\n';
        qInfo().noquote() << "  生成:" << png << "size" << img.width() << "x" << img.height();
        ++idx;
    }
    manifest.close();
    qInfo().noquote() << "QR_GEN_DONE" << outDir << "count" << idx;
    return 0;
}
