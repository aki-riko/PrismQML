#version 440

// Icon tint shader 图标着色着色器
// Paints the tint color through the source alpha, the same result as the former
// ColorOverlay layer, but sampling the Image texture directly with no offscreen pass.
// 以源图 alpha 绘制着色色，结果与原 ColorOverlay 层一致，但直接采样 Image 纹理、不走离屏渲染。
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec4 tintColor;
};

layout(binding = 1) uniform sampler2D source;

void main() {
    float coverage = texture(source, qt_TexCoord0).a;
    fragColor = vec4(tintColor.rgb * tintColor.a, tintColor.a) * coverage * qt_Opacity;
}
