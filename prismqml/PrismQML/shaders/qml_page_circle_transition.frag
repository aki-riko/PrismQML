#version 440

// QML loading-page single-aperture transition QML 加载页单层光圈过渡
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float progress;
    float aspectRatio;
    float minimumRadius;
    float edgeSoftness;
    float invertMask;
    float borderWidth;
    vec4 borderColor;
};

layout(binding = 1) uniform sampler2D source;

void main() {
    vec2 radialPosition = qt_TexCoord0 - vec2(0.5);
    radialPosition.x *= aspectRatio;

    float distanceToCenter = length(radialPosition);
    float maximumRadius = length(vec2(0.5 * aspectRatio, 0.5))
        + edgeSoftness * 2.0;
    float apertureRadius = mix(
        minimumRadius,
        maximumRadius,
        clamp(progress, 0.0, 1.0)
    );
    float insideAperture = 1.0 - smoothstep(
        apertureRadius - edgeSoftness,
        apertureRadius + edgeSoftness,
        distanceToCenter
    );
    float maskAlpha = mix(insideAperture, 1.0 - insideAperture, invertMask);

    vec4 pageColor = texture(source, qt_TexCoord0) * (maskAlpha * qt_Opacity);
    float borderHalfWidth = max(borderWidth, 0.0) * 0.5;
    float borderAlpha = 1.0 - smoothstep(
        max(borderHalfWidth - edgeSoftness, 0.0),
        borderHalfWidth + edgeSoftness,
        abs(distanceToCenter - apertureRadius)
    );
    vec4 outlineColor = vec4(
        borderColor.rgb * (borderAlpha * borderColor.a * qt_Opacity),
        borderAlpha * borderColor.a * qt_Opacity
    );

    // Paint the shared outline above the page snapshot while preserving
    // premultiplied-alpha output. 在页面快照上方绘制共享描边并保持预乘透明度。
    fragColor = outlineColor + pageColor * (1.0 - outlineColor.a);
}
