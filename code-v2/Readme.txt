步骤:
1. 找到想要跑的t01的json, 保存到txt文件
可以通过命令行完成, eg. 获取前500个json文件
ls *-t01.json | head -500 > ../sample-500.txt

2. 提取-t01.json 和与之对应的非t01的json文件
select.py: 根据txt文件里的内容, 将一些t01.json文件从原始目录取出放到新的目录

3. 执行step1.py, 下载并分割mp3
4. 执行step2.py, 处理mp3获取std和mean

另外:
* 如果step2.py处理失败,则需要再次执行即可(会自动跳过已经处理过的和已经处理失败的)

* auto.sh 自动化的脚本

* 配合cron计划,可以每隔5分钟去检测脚本是否运行, 没有的话就执行脚本 (crontab -e)
# every minutes check whether to run auto.sh
*/5 * * * * /bin/bash /home/ubuntu/tmp/audio/auto.sh
