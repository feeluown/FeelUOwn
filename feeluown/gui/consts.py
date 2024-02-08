import sys

if sys.platform == 'win32':
    # By default, it uses SimSun(宋体) on windows, which is a little ugly.
    # "Segoe UI Symbol" is used to render charactor symbols.
    # "Microsoft Yahei" is used to render chinese (and english).
    # Choose a default sans-serif font when the first two fonts do not work,
    FontFamilies = ['Segoe UI Symbol', 'Microsoft YaHei', 'sans-serif']
elif sys.platform == 'darwin':
    FontFamilies = ['arial', 'Hiragino Sans GB', 'sans-serif']
else:
    FontFamilies = [
        'Helvetica Neue', 'Helvetica', 'Arial', 'Microsoft Yahei', 'Hiragino Sans GB',
        'Heiti SC', 'WenQuanYi Micro Hei', 'sans-serif'
    ]

# The width of ScrollBar on macOS is about 10.
ScrollBarWidth = 10
