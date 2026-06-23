#version 440

layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    // 自定义uniform（从QML的property传入，使用float避免对齐问题）
    float windowRatioX;  // 窗口X方向占比
    float windowRatioY;  // 窗口Y方向占比
    float cornerRatio;   // 圆角占比
    float shadowSigma;   // 阴影扩散系数
};

layout(binding = 1) uniform sampler2D source;

// 圆角矩形SDF（Signed Distance Field）
float roundedBoxSDF(vec2 p, vec2 b, float r) {
    vec2 q = abs(p) - b + r;
    return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r;
}

void main() {
    vec2 uv = qt_TexCoord0;
    
    // 转换到居中坐标系（-1到1）
    vec2 pos = (uv - 0.5) * 2.0;
    
    // 窗口在整个shader区域中的比例（从QML动态传入）
    vec2 windowSize = vec2(windowRatioX, windowRatioY);
    float cornerRadius = cornerRatio;
    
    // 计算到窗口边缘的距离（正数=在外面，负数=在里面）
    float dist = roundedBoxSDF(pos, windowSize, cornerRadius);
    
    // 只在窗口外部渲染阴影
    if (dist <= 0.0) {
        fragColor = vec4(0.0);
        return;
    }
    
    // 高斯衰减：距离越远越透明
    // sigma控制阴影的扩散程度（从QML传入）
    float gaussian = exp(-(dist * dist) / (2.0 * shadowSigma * shadowSigma));
    
    // Windows风格：靠近窗口处浓，远处淡
    float alpha = 0.2 * gaussian * qt_Opacity;
    
    fragColor = vec4(0.0, 0.0, 0.0, alpha);
}
