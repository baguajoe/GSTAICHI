const webpack = require('webpack');
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
require('dotenv').config();

// Only these variables are exposed to the frontend bundle. Everything else in
// .env / the build environment (DB credentials, JWT/encryption secrets, R2 keys,
// PayPal client secret, ...) is backend-only and must never be listed here:
// whatever is listed is inlined into public/bundle.js and readable by anyone.
const FRONTEND_ENV = {
  required: ['BACKEND_URL'],
  optional: ['BASENAME', 'PAYPAL_CLIENT_ID']
};
const SECRET_LOOKING = /SECRET|PASSWORD|PRIVATE|TOKEN|DATABASE|ENCRYPTION|_KEY(_ID)?$/;

const frontendEnv = () => {
  const names = [...FRONTEND_ENV.required, ...FRONTEND_ENV.optional];
  const suspicious = names.filter(name => SECRET_LOOKING.test(name));
  if (suspicious.length) throw new Error(`Refusing to expose secret-looking variables to the frontend: ${suspicious.join(', ')}`);
  const missing = FRONTEND_ENV.required.filter(name => !process.env[name]);
  if (missing.length) throw new Error(`Missing frontend environment variable(s): ${missing.join(', ')}`);
  return Object.fromEntries(names.map(name => [name, process.env[name] || '']));
};

module.exports = {
  entry: [
    './src/front/js/index.js'
  ],
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'public'),
    publicPath: '/'
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: ['babel-loader']
      },
      {
        test: /\.(css|scss)$/, use: [{
          loader: "style-loader" // creates style nodes from JS strings
        }, {
          loader: "css-loader" // translates CSS into CommonJS
        }]
      }, //css only files
      {
        test: /\.(png|svg|jpg|gif|jpeg|webp)$/, use: {
          loader: 'file-loader',
          options: { name: '[name].[ext]' }
        }
      }, //for images
      { test: /\.woff($|\?)|\.woff2($|\?)|\.ttf($|\?)|\.eot($|\?)|\.svg($|\?)/, use: ['file-loader'] } //for fonts
    ]
  },
  resolve: {
    extensions: ['*', '.js']
  },
  plugins: [
    new HtmlWebpackPlugin({
      favicon: 'GSL.ico',
      template: 'template.html'
    }),
    // Replaces the whole `process.env` object, so any other process.env.X in
    // frontend code becomes undefined instead of leaking a build-time value.
    new webpack.DefinePlugin({ 'process.env': JSON.stringify(frontendEnv()) })
  ]
};