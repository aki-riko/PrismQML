#version 440

// Neumorphic inset SDF shader 新拟态圆角内阴影距离场着色器
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float itemWidth;
    float itemHeight;
    float cornerRadius;
    float shadowDepth;
    float shadowSoftness;
    float darkR;
    float darkG;
    float darkB;
    float darkOpacity;
    float lightR;
    float lightG;
    float lightB;
    float lightOpacity;
};

float roundedBoxSDF(vec2 point, vec2 halfSize, float radius) {
    vec2 q = abs(point) - halfSize + radius;
    return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - radius;
}

void main() {
    vec2 halfSize = vec2(itemWidth, itemHeight) * 0.5;
    float radius = min(cornerRadius, min(halfSize.x, halfSize.y));
    vec2 point = (qt_TexCoord0 - vec2(0.5)) * vec2(itemWidth, itemHeight);
    float distanceToSurface = roundedBoxSDF(point, halfSize, radius);

    // Outside the rounded surface remains transparent 保留圆角外部透明
    if (distanceToSurface > 0.0) {
        fragColor = vec4(0.0);
        return;
    }

    float insideDepth = -distanceToSurface;
    float softness = max(shadowSoftness, 0.001);
    float edgeFade = exp(-insideDepth / softness);
    float sampleStep = max(shadowDepth, 1.0);
    float dx = roundedBoxSDF(point + vec2(sampleStep, 0.0), halfSize, radius)
             - roundedBoxSDF(point - vec2(sampleStep, 0.0), halfSize, radius);
    float dy = roundedBoxSDF(point + vec2(0.0, sampleStep), halfSize, radius)
             - roundedBoxSDF(point - vec2(0.0, sampleStep), halfSize, radius);
    vec2 gradient = vec2(dx, dy);
    float gradientLength = length(gradient);
    // Avoid the zero-gradient center and keep the shadow near the edge.
    // 避免中心零梯度伪影，并将阴影限制在边缘附近。
    if (gradientLength < 0.001 || insideDepth > softness * 1.5) {
        fragColor = vec4(0.0);
        return;
    }
    vec2 outwardNormal = gradient / gradientLength;

    // Light comes from the upper-left: darken upper/left edges and lift lower/right edges.
    // 光源来自左上：左上边缘压暗，右下边缘提亮。
    float darkWeight = clamp(max(-outwardNormal.x, -outwardNormal.y), 0.0, 1.0);
    float lightWeight = clamp(max(outwardNormal.x, outwardNormal.y), 0.0, 1.0);
    float darkAlpha = edgeFade * darkWeight * darkOpacity * qt_Opacity;
    float lightAlpha = edgeFade * lightWeight * lightOpacity * qt_Opacity;
    float alpha = min(darkAlpha + lightAlpha, 1.0);
    vec3 color = vec3(darkR, darkG, darkB) * darkAlpha
               + vec3(lightR, lightG, lightB) * lightAlpha;

    fragColor = vec4(color, alpha);
}
