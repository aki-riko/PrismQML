#version 440

// Window close water-ripple fragment shader 窗口关闭自然水波片元着色器
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float progress;
    float aspectRatio;
    float tailLength;
    float waveFrequency;
    float waveDispersion;
    float waveDamping;
    float waveAmplitude;
    float highlightStrength;
    float frontSoftness;
    float frontRefractionWidth;
    float crestSharpness;
    float rippleOpacity;
    float finishFadeStart;
};

layout(binding = 1) uniform sampler2D source;

void main() {
    vec2 uv = qt_TexCoord0;
    vec2 radialPosition = uv - vec2(0.5);
    radialPosition.x *= aspectRatio;

    float distanceToCenter = length(radialPosition);
    float maximumRadius = length(vec2(0.5 * aspectRatio, 0.5));
    float waveRadius = progress * (maximumRadius + tailLength);
    float behindFront = waveRadius - distanceToCenter;
    float signedFrontDistance = -behindFront;
    float rippleDistance = max(behindFront, 0.0);
    float tailRatio = clamp(rippleDistance / max(tailLength, 0.0001), 0.0, 1.0);
    float tailMask = 1.0 - smoothstep(0.82, 1.0, tailRatio);
    float envelope = exp(-rippleDistance * waveDamping) * tailMask;
    float wavePhase = rippleDistance * waveFrequency
        * (1.0 + waveDispersion * tailRatio);
    float waveHeight = cos(wavePhase);
    float waveSlope = sin(wavePhase);
    float rippleCrest = pow(abs(waveHeight), crestSharpness);

    float exteriorAlpha = smoothstep(
        -frontSoftness,
        frontSoftness,
        signedFrontDistance
    );
    float interiorWeight = 1.0 - exteriorAlpha;
    float rippleAlpha = rippleCrest * envelope * rippleOpacity * interiorWeight;

    float frontRatio = signedFrontDistance
        / max(frontRefractionWidth, 0.0001);
    float frontEnvelope = 1.0 - smoothstep(0.0, 1.0, abs(frontRatio));
    float frontSlope = frontRatio * frontEnvelope;
    float trailingSlope = waveSlope * interiorWeight * envelope;
    float surfaceSlope = frontSlope + trailingSlope;

    vec2 radialDirection = distanceToCenter > 0.0001
        ? radialPosition / distanceToCenter
        : vec2(0.0);
    vec2 uvDirection = vec2(radialDirection.x / aspectRatio, radialDirection.y);
    float distortionEnvelope = max(frontEnvelope, interiorWeight * envelope);
    vec2 sampleUv = clamp(
        uv + uvDirection * surfaceSlope * distortionEnvelope * waveAmplitude,
        vec2(0.0),
        vec2(1.0)
    );
    vec4 sourceColor = texture(source, sampleUv);
    sourceColor.rgb = clamp(
        sourceColor.rgb * (1.0 + surfaceSlope * highlightStrength),
        vec3(0.0),
        vec3(1.0)
    );

    float finishAlpha = 1.0 - smoothstep(finishFadeStart, 1.0, progress);
    float sourceCoverage = sourceColor.a * exteriorAlpha;
    float clearRippleAlpha = rippleAlpha * (1.0 - sourceCoverage);
    vec3 rippleColor = waveHeight >= 0.0 ? vec3(1.0) : vec3(0.0);
    vec3 outputColor = sourceColor.rgb * exteriorAlpha
        + rippleColor * clearRippleAlpha;
    float outputAlpha = sourceCoverage + clearRippleAlpha;
    fragColor = vec4(outputColor, outputAlpha) * (finishAlpha * qt_Opacity);
}
