import xlrd
import xlwt
import paramiko
import os
import time
import re

CSheet = xlrd.open_workbook(r'E:\工控机升级\工控机程序更新\已上线设备6.24yjq整理.xlsx')
data = CSheet.sheets()[0]
nrow = data.nrows

FailedList = []
notCompleteList = []
ntpErr = []

# 检查路径是否存在
def _is_exists(path, function):
    path = path.replace('\\', '/')
    try:
        function(path)
    except Exception as error:
        return False
    else:
        return True


# 检查文件是否上传完整
def _is_equal_file_sizes(local,remote,ssh):
    localSize = os.path.getsize(local)
    stdin,stdout,stderr = ssh.exec_command("du -b %s"%(remote))
    out = str(stdout.read())
    ss = re.findall(r"\d+",out)[0]
    remoteSize = int(ss)

    if remoteSize == localSize:
        return True
    else :
        return False


# 拷贝文件
def _copy(ssh, sftp, local, remote):
    # 判断remote是否是目录
    if _is_exists(remote, function=sftp.chdir):
        # 是，获取local路径中的最后一个文件名拼接到remote中
        filename = os.path.basename(os.path.normpath(local))
        remote = os.path.join(remote, filename).replace('\\', '/')
    # 如果local为目录
    if os.path.isdir(local):
        # 在远程创建相应的目录
        _is_exists(remote, function=sftp.mkdir)
        # 遍历local
        for file in os.listdir(local):
            # 取得file的全路径
            localfile = os.path.join(local, file).replace('\\', '/')
            # 深度递归_copy()
            _copy(ssh=ssh, sftp=sftp, local=localfile, remote=remote)
    # 如果local为文件
    if os.path.isfile(local):
        try:
            ssh.exec_command("rm -rf %s"%(remote))
            time.sleep(1)
            sftp.put(local, remote)

            ssh.exec_command("chmod 777 %s"%(remote))
            # ssh.exec_command("kill -9 $(ps aux|grep 'CenterServer.exe$'|awk '{print$2}')")

        except Exception as error:
            print(error)
            print('[put]', local, '==>', remote, 'FAILED')
        else:
            isComplete = _is_equal_file_sizes(local=local,remote=remote,ssh=ssh)  # 根据文件大小判断文件是否上传完整
            if isComplete == False :
                print("%s文件传输不完整！"(local))
            else :
                print('[put]', local, '==>', remote, 'SUCCESSED')


for i in range(1, nrow):
    ip = data.row_values(i)[0]

    try:
        transport = paramiko.Transport((ip, 22))
        transport.connect(username='root', password='dhERIS@2018*#')

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())   # 自动添加策略，保存服务器的主机名和秘钥信息，不添加，不在本地hnow_hosts文件中的记录将无法连接
        ssh._transport = transport

        print("%s 连接成功" % (ip))

        sftp = paramiko.SFTPClient.from_transport(transport)
        # sftp.put('window.txt','/tmp/Window.txt')        # 将本地Window.txt文件上传到/tmp/Windwos.txt

        _copy(ssh=ssh, sftp=sftp, local='E:\\工控机升级\\工控机程序更新\\ntp同步文件\\ntp.conf', remote='/etc/')
        _copy(ssh=ssh, sftp=sftp, local='E:\\工控机升级\\工控机程序更新\\ntp同步文件\\eris', remote='/mnt/soft/softv/')

        # 关闭chronyd自启动
        ssh.exec_command("systemctl disable chronyd")
        stdin,stdout,stderror = ssh.exec_command("systemctl is-enabled chronyd")
        # print("chronyd 自启动状态为：",stdout.read().decode())

        ssh.exec_command("systemctl enable ntpd")   # 开启ntpd自启动

        ssh.exec_command("service ntpd restart")

        stdin,stdout,stderror =  ssh.exec_command("systemctl status ntpd | grep active | awk '{print$2}'")
        # print(stdout.read().decode())
        status = stdout.read().decode()

        if status == 'inactive':
            ntpErr.append(ip)
        

    except Exception as reason:
        print(reason)
        FailedList.append(ip)

print("连接失败工控机：")
for j in FailedList:
    print(j)


print("ntp启动异常：")
for j in ntpErr:
    print(j)


