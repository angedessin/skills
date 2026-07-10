# deployments — スキル配置先レジストリ（マスター専用・配布しない）

# skill-harvest / scripts/check_deploy_drift.py（レジストリモード）が読む配置先の一覧。
# 配置先プロジェクトの絶対パスを 1 行 1 件で列挙する。# 始まりはコメント、空行は無視。
# スキル単位の記録は持たない — どのスキルが配置されているかは各配置先の
# metadata.source-commit から発見する（レジストリの二重管理を避ける）。
#
# 例:
# /Users/kentaro/work/my-frontend-app
# /Users/kentaro/work/another-project

# （配置先を追加したらここに 1 行で登録する。starter-kit.md の配置手順を参照）
