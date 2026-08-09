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

    fragColor = texture(source, qt_TexCoord0) * (maskAlpha * qt_Opacity);
}
