# deployments — スキル配置先レジストリ（雛形・マスター専用）

# これは雛形。実体の deployments.md は .gitignore でローカル限定にしている
# （中身がこのマシンでしか意味を持たない絶対パス＝ユーザー名・ローカル構造を含むため、
#  git 追跡すると push 先にローカルパスが漏れる）。
# 初回はこのファイルを deployments.md にコピーして使う:
#   cp deployments.example.md deployments.md
# （deploy_skills.py は deployments.md が無ければ自動作成もするので、コピーは任意）
#
# skill-harvest / scripts/check_deploy_drift.py（レジストリモード）が読む配置先の一覧。
# 配置先プロジェクトの絶対パスを 1 行 1 件で列挙する。# 始まりはコメント、空行は無視。
# スキル単位の記録は持たない — どのスキルが配置されているかは各配置先の
# metadata.source-commit から発見する（レジストリの二重管理を避ける）。
#
# 例:
# /path/to/my-frontend-app
# /path/to/another-project

# （配置先を追加したら deployments.md に 1 行で登録する。starter-kit.md の配置手順を参照）
