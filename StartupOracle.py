import cx_Oracle
import xlrd
import paramiko

Sheet = xlrd.open_workbook(r'C:\Users\Administrator\Desktop\Python\工控机程序更新\IPList.xlsx')
data = Sheet.sheets()[0]
nrow = data.nrows

TimeoutList = []

# 获取连接信息
def _create_ssh(ip):
    transport = paramiko.Transport((ip, 22))
    transport.connect(username='root', password='dhERIS@2018*#')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())   # 自动添加策略，保存服务器的主机名和秘钥信息，不添加，不在本地hnow_hosts文件中的记录将无法连接
    ssh._transport = transport
    sftp = paramiko.SFTPClient.from_transport(transport)

    return ssh,sftp

for i in range(1, nrow):
    ip = data.row_values(i)[0]
    conInfo = "ERIS/ERIS@%s:1521/ERIS"%(ip)

    try:
        ssh,sftp = _create_ssh(ip)
        print("%s 连接成功！"%(ip))

        ssh.exec_command("su - oracle;sqlplus / as sysdba;")

    except Exception as err:
        print("%s 连接超时： "%(ip),err)
        TimeoutList.append(ip)