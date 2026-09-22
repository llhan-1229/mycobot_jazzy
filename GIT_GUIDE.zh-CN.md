# Git 更新、上传与回退说明

适用于本仓库当前配置：远程仓库为 `origin`，默认分支为 `main`，仓库目录为 `/home/lh/ros2_ws/src/mycobot_ros2`。

## 日常更新并上传

```bash
cd /home/lh/ros2_ws/src/mycobot_ros2
git status
git branch --show-current
git diff
git diff --check
```

确认修改范围后提交并上传：

```bash
git add <修改的文件>
git status
git commit -m "简短描述本次修改"
git push origin main
```

如果确认所有工作区修改都属于本次任务，可以使用 `git add -A`，但不要在未检查 `git status` 时使用它，以免提交临时文件或其他人的修改。

## 上传前同步远程

```bash
git fetch origin
git log --oneline --decorate --graph --all -20
git pull --rebase origin main
```

变基冲突处理：编辑冲突文件后执行 `git add <已解决的文件>`，再执行 `git rebase --continue`。放弃本次变基：`git rebase --abort`。

## 查看历史和远程状态

```bash
git status -sb
git log --oneline --decorate --graph -20
git show --stat HEAD
git remote -v
```

当前功能版本提交为 `39697e2 feat: add color-aware red and blue cylinder picking`。

## 回退未提交的修改

只撤销某个文件：

```bash
git restore -- <文件路径>
```

撤销全部未提交修改前，先检查 `git status --short` 和 `git diff --name-only`。确认不需要后才执行：

```bash
git restore --worktree --staged .
```

这个操作会丢弃未提交内容。取消暂存但保留文件修改：`git restore --staged <文件路径>`。

## 回退最近一次本地提交

保留修改并撤销提交：

```bash
git reset --soft HEAD~1
```

撤销提交、保留修改但取消暂存：

```bash
git reset HEAD~1
```

撤销提交并丢弃文件修改：

```bash
git reset --hard HEAD~1
```

`--hard` 会丢失未保存内容，通常优先使用 `--soft` 或普通 `reset`。

## 已上传后的回退

已推送到远程的提交，推荐创建反向提交，不要改写共享历史：

```bash
git log --oneline -10
git revert <要撤销的commit-id>
git push origin main
```

撤销最近一次提交可使用 `git revert HEAD`。冲突时解决文件后执行 `git add <已解决的文件>` 和 `git revert --continue`；放弃本次回退使用 `git revert --abort`。

## 找回误删或误回退的提交

```bash
git reflog --date=local -20
git switch -c recovery/<简短名称> <commit-id>
```

先在恢复分支检查内容，再决定合并或使用 `git revert` 恢复到 `main`。

## 不建议直接使用的命令

除非团队明确约定并确认没有其他人基于远程分支开发，否则不要使用：

```bash
git push --force
git reset --hard origin/main
git clean -fd
```

这些命令可能改写远程历史或删除未跟踪文件。上传失败时，先执行 `git status`、`git fetch origin`，再根据具体错误处理。
