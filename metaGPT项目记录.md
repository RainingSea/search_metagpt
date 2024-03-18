### HumanEval

测试编号 0 - 14

| 状态 |  #   |
| :--: | :--: |
| 失败 |  5   |
| 成功 |  10  |

##### gpt-3.5-turbo

![image-20240306201534903](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240306201534903.png)

##### metagpt + gpt4-1106-preview

![image-20240306201213424](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240306201213424.png)

#### 具体错误用例

gpt3.5 失败用例为：1，6，10

metagpt 失败用例为：1，6，**8，9，**10

#### 原因

##### 用例 8

![image-20240306203252344](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240306203252344.png)

![image-20240306203742884](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240306203742884.png)

没有考虑额外需求，漏过了0个元素乘积为1这个额外要求

##### 用例 9

![image-20240306202501739](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240306202501739.png)

metagpt 引入 deque() 数据结构，但没有初始化这个数据结构

#### 暂时总结

metagpt + gpt4 代码特点：代码量少，但逻辑更为复杂

在 metagpt 现有的结构设计和 prompt 设计下，无法达到目标效果



### 项目生成

#### audio_recorder_app

ES6 语法错误

![image-20240307100105033](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240307100105033.png)

![image-20240307100140918](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240307100140918.png)

#### audio recorder web app

没有实现功能，幻觉问题，使用自己没有定义的对象

![image-20240307100514894](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240307100514894.png)

#### drawing board tool

功能未实现

![image-20240307100651681](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240307100651681.png)

#### game 2048

使用了 kivy库，然后没有实现功能

![image-20240307103809673](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240307103809673.png)

#### interactive weather dashboard

幻觉问题，调用自己没有实现的功能

![image-20240307104342609](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240307104342609.png)

#### pixel art creator

幻觉

![image-20240307104606511](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240307104606511.png)

![image-20240307104552884](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240307104552884.png)

对两个成功的项目分析，prompt里加 simple 更有可能成功，限制gpt不调用复杂的逻辑（目前成功率较低）
