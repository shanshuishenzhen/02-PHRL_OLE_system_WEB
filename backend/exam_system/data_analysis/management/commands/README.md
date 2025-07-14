# 数据分析管理命令

本目录包含用于管理数据分析任务的Django管理命令。这些命令可以通过`python manage.py <命令名称>`来执行。

## 命令列表

### 1. 处理分析任务

```bash
python manage.py process_analysis_tasks [--limit LIMIT] [--timeout TIMEOUT] [--continuous] [--interval INTERVAL]
```

**功能**：处理待处理状态的分析任务。

**参数**：
- `--limit`：一次处理的最大任务数量（默认：10）
- `--timeout`：任务处理超时时间（秒）（默认：300）
- `--continuous`：持续运行模式，处理完一批任务后等待新任务
- `--interval`：持续模式下的检查间隔（秒）（默认：60）

**示例**：
```bash
# 处理最多5个任务
python manage.py process_analysis_tasks --limit 5

# 持续运行模式，每30秒检查一次新任务
python manage.py process_analysis_tasks --continuous --interval 30
```

### 2. 清理分析任务

```bash
python manage.py cleanup_analysis_tasks [--completed-days DAYS] [--failed-days DAYS] [--dry-run]
```

**功能**：清理过期的分析任务数据。

**参数**：
- `--completed-days`：保留已完成任务的天数（默认：30）
- `--failed-days`：保留失败任务的天数（默认：7）
- `--dry-run`：仅显示将被删除的任务，不实际删除

**示例**：
```bash
# 删除30天前的已完成任务和7天前的失败任务
python manage.py cleanup_analysis_tasks

# 仅显示将被删除的任务，不实际删除
python manage.py cleanup_analysis_tasks --dry-run

# 自定义保留时间
python manage.py cleanup_analysis_tasks --completed-days 60 --failed-days 14
```

### 3. 重试失败任务

```bash
python manage.py retry_failed_tasks [--task-id TASK_ID] [--all]
```

**功能**：重试失败的分析任务。

**参数**：
- `--task-id`：要重试的特定任务ID
- `--all`：重试所有失败的任务

**示例**：
```bash
# 重试特定任务
python manage.py retry_failed_tasks --task-id 123

# 重试所有失败任务
python manage.py retry_failed_tasks --all
```

### 4. 生成任务统计

```bash
python manage.py generate_task_stats [--group-by {day,week,month}] [--days DAYS] [--output FILE]
```

**功能**：生成分析任务的统计报告。

**参数**：
- `--group-by`：统计分组方式（day/week/month）（默认：day）
- `--days`：统计最近几天的数据（默认：30）
- `--output`：输出文件路径（默认输出到控制台）

**示例**：
```bash
# 按天统计最近30天的任务
python manage.py generate_task_stats

# 按周统计最近60天的任务，并输出到文件
python manage.py generate_task_stats --group-by week --days 60 --output stats.txt
```

### 5. 创建分析任务

```bash
python manage.py create_analysis_task --type TYPE --name NAME --admin-username USERNAME [--params PARAMS] [--exam-id ID] [--student-id ID] [...]
```

**功能**：创建新的分析任务。

**参数**：
- `--type`：分析任务类型（exam/student/question/knowledge/class/department/custom）
- `--name`：分析任务名称
- `--admin-username`：管理员用户名（作为任务创建者）
- `--params`：任务参数，JSON格式字符串
- `--exam-id`：考试ID（用于考试分析）
- `--student-id`：学生ID（用于学生分析）
- `--class-id`：班级ID（用于班级分析）
- `--department-id`：院系ID（用于院系分析）
- `--question-id`：题目ID（用于题目分析）
- `--knowledge-id`：知识点ID（用于知识点分析）

**示例**：
```bash
# 创建考试分析任务
python manage.py create_analysis_task --type exam --name "期末考试分析" --admin-username admin --exam-id 123

# 创建学生分析任务
python manage.py create_analysis_task --type student --name "学生学习情况分析" --admin-username teacher1 --student-id 456

# 使用自定义参数创建任务
python manage.py create_analysis_task --type custom --name "自定义分析" --admin-username admin --params '{"custom_param":"value"}'
```

### 6. 检查卡住的任务

```bash
python manage.py check_stalled_tasks [--hours HOURS] [--dry-run] [--auto-retry]
```

**功能**：检查并重置卡在处理中状态的分析任务。

**参数**：
- `--hours`：处理时间超过多少小时视为卡住（默认：1）
- `--dry-run`：仅显示将被重置的任务，不实际重置
- `--auto-retry`：自动将卡住的任务重置为待处理状态（否则标记为失败）

**示例**：
```bash
# 检查处理时间超过2小时的任务
python manage.py check_stalled_tasks --hours 2

# 仅显示卡住的任务，不实际重置
python manage.py check_stalled_tasks --dry-run

# 自动重试卡住的任务
python manage.py check_stalled_tasks --auto-retry
```

### 7. 导出分析结果

```bash
python manage.py export_analysis_results [--task-id TASK_ID] [--type TYPE] [--status STATUS] [--format FORMAT] [--output-dir DIR] [--days DAYS]
```

**功能**：导出分析任务结果为CSV或JSON格式。

**参数**：
- `--task-id`：要导出的分析任务ID
- `--type`：要导出的分析任务类型（默认：all）
- `--status`：要导出的任务状态（默认：completed）
- `--format`：导出格式（csv/json）（默认：csv）
- `--output-dir`：导出文件保存目录（默认：./exports）
- `--days`：仅导出最近几天的任务结果

**示例**：
```bash
# 导出特定任务的结果
python manage.py export_analysis_results --task-id 123

# 导出所有考试分析任务的结果为JSON格式
python manage.py export_analysis_results --type exam --format json

# 导出最近7天的已完成任务结果
python manage.py export_analysis_results --days 7 --output-dir /path/to/exports
```

### 8. 优化分析数据库

```bash
python manage.py optimize_analysis_db [--vacuum] [--reindex] [--analyze] [--optimize-tables] [--archive-old] [--days DAYS] [--dry-run]
```

**功能**：优化分析任务数据库表，提高系统性能。

**参数**：
- `--vacuum`：执行VACUUM操作（仅适用于PostgreSQL）
- `--reindex`：重建索引（仅适用于PostgreSQL）
- `--analyze`：更新统计信息（仅适用于PostgreSQL）
- `--optimize-tables`：优化表（仅适用于MySQL）
- `--archive-old`：归档旧的分析任务结果
- `--days`：归档多少天前的任务（默认：90）
- `--dry-run`：仅显示将执行的操作，不实际执行

**示例**：
```bash
# PostgreSQL优化
python manage.py optimize_analysis_db --vacuum --reindex --analyze

# MySQL优化
python manage.py optimize_analysis_db --optimize-tables

# 归档90天前的任务结果
python manage.py optimize_analysis_db --archive-old

# 仅显示将执行的操作，不实际执行
python manage.py optimize_analysis_db --vacuum --archive-old --days 60 --dry-run
```

### 9. 导入分析任务

```bash
python manage.py import_analysis_tasks FILE_PATH [--format FORMAT] [--admin-username USERNAME] [--dry-run] [--skip-errors]
```

**功能**：从CSV或JSON文件批量导入分析任务。

**参数**：
- `FILE_PATH`：CSV或JSON文件路径
- `--format`：文件格式（csv/json）（如果未指定，将根据文件扩展名自动判断）
- `--admin-username`：管理员用户名（作为任务创建者，如果文件中未指定）
- `--dry-run`：仅验证导入数据，不实际创建任务
- `--skip-errors`：遇到错误时跳过并继续处理其他任务

**示例**：
```bash
# 从CSV文件导入任务
python manage.py import_analysis_tasks tasks.csv

# 从JSON文件导入任务，指定管理员用户
python manage.py import_analysis_tasks tasks.json --admin-username admin

# 仅验证导入数据，不实际创建任务
python manage.py import_analysis_tasks tasks.csv --dry-run

# 遇到错误时跳过并继续处理其他任务
python manage.py import_analysis_tasks tasks.json --skip-errors
```

## 定时任务配置

建议将以下命令配置为定时任务（使用crontab或Windows计划任务）：

1. **处理分析任务**（每分钟运行）：
```bash
*/1 * * * * cd /path/to/project && python manage.py process_analysis_tasks --limit 5
```

2. **检查卡住的任务**（每小时运行）：
```bash
0 * * * * cd /path/to/project && python manage.py check_stalled_tasks --auto-retry
```

3. **清理过期任务**（每天凌晨运行）：
```bash
0 0 * * * cd /path/to/project && python manage.py cleanup_analysis_tasks
```

4. **优化数据库**（每周日凌晨运行）：
```bash
0 0 * * 0 cd /path/to/project && python manage.py optimize_analysis_db --vacuum --reindex --analyze --archive-old
```

5. **生成任务统计**（每天凌晨运行）：
```bash
0 1 * * * cd /path/to/project && python manage.py generate_task_stats --output /path/to/stats/task_stats_$(date +\%Y\%m\%d).txt
```

## 注意事项

1. 在生产环境中，建议使用`--limit`参数限制一次处理的任务数量，以避免系统过载。
2. 对于长时间运行的命令（如`process_analysis_tasks --continuous`），建议使用进程管理工具（如Supervisor）来管理。
3. 数据库优化命令应在系统负载较低时运行。
4. 在执行可能影响数据的命令前，建议先使用`--dry-run`参数进行测试。
5. 所有命令都会记录详细日志，可以通过Django的日志系统查看。