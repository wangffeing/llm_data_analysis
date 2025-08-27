const path = require('path');

module.exports = {
  babel: {
    presets: [
      [
        '@babel/preset-env',
        {
          targets: {
            chrome: '83'
          },
          useBuiltIns: 'entry',
          corejs: 3,
          modules: false,
          loose: true
        }
      ],
      [
        '@babel/preset-react',
        {
          runtime: 'automatic'  // Add this line
        }
      ],
      '@babel/preset-typescript'
    ],
    plugins: [
      // 显式配置这些插件，确保 loose 模式一致
      ["@babel/plugin-transform-class-properties", { "loose": true }],
      ["@babel/plugin-transform-private-methods", { "loose": true }],
      ["@babel/plugin-transform-private-property-in-object", { "loose": true }]
    ]
  },
  webpack: {
    configure: (webpackConfig) => {
      // 只保留必要的模块解析规则
      webpackConfig.module.rules.push({
        test: /\.m?js$/,
        resolve: {
          fullySpecified: false
        },
        type: "javascript/auto"
      });
      
      // 确保扩展名解析正确
      webpackConfig.resolve.extensions = [
        '.tsx', '.ts', '.js', '.jsx', '.mjs',
        ...webpackConfig.resolve.extensions
      ];
      
      // 忽略 source-map-loader 警告
      webpackConfig.ignoreWarnings = [
        function ignoreSourcemapsloaderWarnings(warning) {
          return (
            warning.module &&
            warning.module.resource &&
            warning.module.resource.includes('node_modules') &&
            warning.details &&
            warning.details.includes('source-map-loader')
          );
        },
      ];

      return webpackConfig;
    },
  },
};