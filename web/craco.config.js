const path = require('path');

module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // 1. 添加关键的模块解析规则（基于外部链接的解决方案）
      webpackConfig.module.rules.push({
        test: /\.m?js$/,
        resolve: {
          fullySpecified: false
        },
        // 可选：完全禁用 .mjs 文件的不同行为
        type: "javascript/auto"
      });
      
      // 2. 专门处理 @antv 包的规则
      webpackConfig.module.rules.push({
        test: /\.m?js$/,
        include: /node_modules\/@antv/,
        resolve: {
          fullySpecified: false
        },
        type: "javascript/auto"
      });
      
      // 3. 强制使用 CommonJS 版本的别名
      webpackConfig.resolve.alias = {
        ...webpackConfig.resolve.alias,
        '@antv/gpt-vis': path.resolve(__dirname, 'node_modules/@antv/gpt-vis/dist/cjs'),
      };
      
      // 4. 确保扩展名解析正确
      webpackConfig.resolve.extensions = [
        '.tsx', '.ts', '.js', '.jsx', '.mjs',
        ...webpackConfig.resolve.extensions
      ];
      
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