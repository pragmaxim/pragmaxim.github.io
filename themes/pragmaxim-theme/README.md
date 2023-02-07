1. Install Hugo by following https://gohugo.io/getting-started/installing/

2. Run :
```
    hugo new site <website-name>
    cd <website-name>/themes/
    git clone https://github.com/pragmaxim/pragmaxim-hugo-theme.git
    cd ..
    cp themes/pragmaxim-theme/example/config.toml ./config.toml
    hugo server -D
```