### 简介

本文档是对于 MetaGPT 执行流程的探索，通过 debug 来观察 Agent 和 环境行为，主要在于观察和项目有关的消息的产生和传递，以及 Agent 对于消息做出的行为

文档中对于SOP流程中与 LLM 关系不大的动作，没有进行过多的细究，这些流程多是文件系统操作和公共操作，在日后进行研究时再拿来细察，本阶段只是记录其功能

### 一、初始化阶段（与metagpt角色行为无关）

python初始化这些代码，只是定义，不执行任何功能

![image-20240313164023329](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313164023329.png)

generate_repo() 启动项目，如果从命令行执行，则从命令行读取参数，如果是文件启动则不用，参数如下：

![image-20240313164338556](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313164338556.png)

雇佣角色：![image-20240313164426961](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313164426961.png)

### 二、执行 SOP 流程

用户输入想要的程序，这里例子是我们想要metagpt生成一个五子棋游戏 gomoku game

首先是系统接收到用户输入后，将用户的 idea 进行广播

![image-20240313164522740](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313164522740.png)

> 特别点1：
>
> 广播的是消息，消息通过 publish_message() 由系统发送给其他 Agent 
>
> ![image-20240313164919883](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313164919883.png)
>
> metagpt 的设定是根据消息里带的 send_to 决定消息发给谁，但实际上这个变量在目前的版本里永远为 All，也就是说消息被发给了所有人，但是它是支持进一步的修改，我们也可以改为只发给指定的人
>
> self.member_addrs 变量如下，可以看到就是初始时添加的所有角色
>
> ![image-20240313165241101](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313165241101.png)
>
> 角色接收消息的方法是 role.put_message() ，将消息放入角色的 msg_buffer 中，这个 buffer 是每个角色有自己的一个，但这里有很多神奇的地方，下文再讲
>
> ![image-20240313165111637](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313165111637.png)
>
> base_env 的 history 仅仅作为记录输出到日志 log，没有其他作用

广播后，由 company（team类型的变量） 的 run 来执行后续流程，实际上是执行 env 的 run() ，每次执行前先检查预算

> 无语，套来套去，接下来还有更多搞笑的套来套去的例子

![image-20240313165451036](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313165451036.png)

env 的 run 方法，顺次启动每个角色的异步 run 函数

这个 future 推测是python异步函数设置的执行完成标志，无实际意义但是异步函数需要，类似于 JavaScript 的 then()

> 说实话，异步函数在 debug 的时候其实很无语，会导致日志顺序错乱

![image-20240313165645654](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313165645654.png)

#### Product Manager

注意，Product Manager 重写了 run 方法，将with_message设置了为false，也就是不会取以往的消息

![image-20240313171848495](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313171848495.png)

因此直接进入到第二个 if 分支中

![image-20240313170123369](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313170123369.png)

第一轮时，Product Manager 没有 message，因此执行 _observe() 

observe 是metagpt的关键功能之一，完成从系统中读取消息，存入记忆的功能

![image-20240313170238818](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313170238818.png)

在上图中:

**news** 代表从角色自己的 msg_buffer 中读取的消息

> 对，就是第一步系统通过执行 role.put_message() 添加到自己 buffer 中的消息，目前确定的是，能够添加到 msg_buffer 的方式仅有系统执行 publish_message() -> role.put_message() 这一种方式

**old_message** 代表角色在将新消息补充到自己的 memory 之前，memory 中存储的所有消息，当然，如果读取到 ignore_memory，则不再读取旧记忆的消息，而是保持空数组

读取完 old_message 之后，才可以把新消息加入到角色自己的 memory 中，成为正儿八经的消息

> 前文中的 msg_buffer 已经完成入队出队，清空了 buffer

加消息需要判断一下，如果消息是自己发的，就不要再加了（为什么会这样之后再回答），否则就加到自己的 memory 里

![image-20240313174350769](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313174350769.png)

**self.rc.news** 是属于角色自己的 news，指新消息 news 中属于自己的部分，且不在 old_message 里的消息，并将这些自己的新消息中第一个取出，作为 **latest_observed_msg** 返回

> 注意和前文的 news 这个临时变量进行区分
>
> 这里如何确定是属于自己的部分？
>
> 要么是角色初始化时定义的监听事件，要么就是角色在消息的 send_to 里。还记得前文里，send_to 在metagpt里目前永远都是 all 吗，all这个关键字只能作为发送的所有，但角色的名字并不是 all，因此，确定消息属于自己只能根据是否是自己的监听事件来看
>
> ![image-20240313171355451](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313171355451.png)
>
> ![image-20240313171429630](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313171429630.png)
>
> ![image-20240313171526765](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313171526765.png)
>
> ![image-20240313171614745](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313171614745.png)
>

至此，observe 结束，相当于对消息进行了处理，接下来就是反应（react）了

![image-20240313171757063](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313171757063.png)

这里有三个模式，分别代表三个处理模式，目前 agent 的处理都采用 think - act 的模式，因此我们只需要关注第一个_react()，实际上metagpt默认总是第一个，其他两个用不到的

react 涉及到两个重要方法，think 和 act 

> 为什么这两个最重要的方法要这么小，就不能通过注释将这两行明显一些。。。

其他的代码行暂时不需要关心，metagpt 角色大多只执行一个动作，除了 Engineer

![image-20240313172129048](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313172129048.png)

首先是 think

![image-20240313172521558](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313172521558.png)

think 这里，两个分支，实际上仔细看第二个 else 分支只为ProductManager 的 PrepareDocument 这一个动作服务（因为都指定了接下来的WritePRD），而 PM 是有两个动作的，另一个动作 WritePRD 就会走第一个分支了

ProductManager的第一个 act 即 PrepareDocument 只涉及到新建文件夹和 git 仓库，这里不再详细展开 act 流程，而是放到第二个动作 WritePRD 再细看

> 咳咳，很熟悉的操作啊，新建文件夹
>
> 这里它还会完成 git 仓库的创建来为后续的增量开发做准备，但 debug 的时候这些步骤特别繁琐，很烦

act 结束后，任务就完成了，而其他角色执行 run 方法因为 observe 不会得到任何消息，所以跳过这一阶段（n_round = 4)

![image-20240313173316664](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313173316664.png)

### 但是，这里目前还不知道什么原因（之后细看），debug 在 act 结束后就直接返回了，跳到下一个角色的 run 里，但还是可以从代码里观察后续的行为【已解決】

角色执行 act 的最后将结果打包为消息，并先放到自己的 memory 中

![image-20240313173759342](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313173759342.png)

随后 react 也返回，返回值和 act 的值一样，然后角色执行广播，这个广播实则是再次调用系统的 publish_message() 

![image-20240313173907411](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313173907411.png)

![image-20240313174005813](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313174005813.png)

### 至此，第一轮结束，第二轮开始

#### ProductManager

书接上文，系统执行 publish_message() 是不是把 ProductManager 的消息又发给了自己，这就是前文提到的把消息发给自己的动作，在下一次 observe 时，ProductManager 会发现自己已经有了这条消息，因此就不会再加一次了

也就是说下图中的这一行内部判断时返回值是 False，所以不会加

![image-20240313174657209](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313174657209.png)

这时，news 是一个新建文件夹的消息，这个消息是被 ProductManager监听的，因此这时，self.rc.news 就会把这条消息加入设为 latest_observed_msg ，从而返回一个正的返回值

接下来还是 react，然后 react里执行 think 和 act 两个方式（剩下的其他的Agent都是这样的流程）

> 坏了，debug按快了，没进 think 这一步，先看 act 这一步吧【已解決】详看前文介绍 think 的时候

act 就到了 prompt 大模型的时候

![image-20240313175303137](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313175303137.png)

上文中一个 self.rc.history 变量，这个变量被输入到action的run中

> 也就是说，角色的 run 指定执行的动作，并处理 memory 和 message 等，而具体的进一步 prompt 大模型是 action 的 run，不要搞混
>
> 这里又到了搞笑的一步，突然窜出来一个角色的 history 变量，我寻思之前只见过环境的 history ，仅仅是为了 debug 用，怎么突然又来一个角色自己的 history？？？之前的流程可没操作过它啊
>
> 然后点进去这个 self.rc.history 变量，看到如下代码：
>
> ![image-20240313175742694](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313175742694.png)
>
> 得，就是取自己的 memory，怪不得之前不用操作，幽默时刻

> 这里debug的时候要注意，在执行 act 之前，由于是异步函数，因此会突然跳转到其他角色里面，但是由于没有收到消息，其他角色还是跳过，然后才能重新回到 ProductManager 的 act 函数里

好，重新回到 WritePRD 的 run 方法中去

set_recursive 方法一步步添加节点（指PRD里面的内容）到 prompt 中去，就是构建对大模型的 prompt，让大模型去补充空位

![image-20240313194222299](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313194222299.png)

补充完后就是这样：

![image-20240313194358466](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313194358466.png)

经过一系列的节点操作等（实际上就是构建一个 prompt，和模板等）

![image-20240313195007588](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313195007588.png)

在 simple_fill 里对大模型 prompt，然后通过 self._aask_v1 来对大模型提问，这个 aask_v1 就是 metagpt 对 gpt 的提问方法，核心就是 gpt 的 chat_completion

![image-20240313195217610](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313195217610.png)

实际的提问也遵循 user content 的模式，每次 prompt 都告诉大模型需要扮演什么角色，然后把文档等作为content来让大模型补充

![image-20240313195341774](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313195341774.png)

随后就是生成消息（message）了，然后广播等操作，这个 WritePRD 就完成了，至此 ProductManager 的任务也完成了

![image-20240313195540422](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313195540422.png)

> 然后会神奇的发现，在我们对大模型提问的时候，是传入了一个 history 参数的，是metagpt以往生成的消息等，但是，这里却没有使用这个参数
>
> ![image-20240313195813282](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313195813282.png)
>
> ![image-20240313195822821](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240313195822821.png)

之后其他角色的流程都遵循这个过程：

1. observe存储消息
2. react，先 think，再 act
3. think 里
4. act 里就是 prompt 大模型
5. 将结果格式化为 message，由系统代为广播 

后续的流程之后慢慢补充，只要把上文中的启动的消息（就是我们输入的需求 idea）替换为每个角色监听的消息，然后流程和 ProductManager 执行流程是一致的 ~

#### 通过 is idle 决定是不是整个流程是否执行完毕【已解决】

idle的流程如下，这里长一些教训，metagpt代码中一些变量，实际上是一个函数，因此在看的时候如果有时候看一个变量觉得带入变量的语境下奇怪的话，那就有可能是函数

> 经典的就是那个角色 history 结果是取所有 memory 的例子

![image-20240315171818684](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315171818684.png)

逐步的取角色，执行完的角色的 is_idle 再由如下过程判断：

![image-20240315172108689](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315172108689.png)

有无消息，有无to_do，有无 msg_buffer

对于PM来说，news是空，todo是空，但msg_buffer不是空

因此返回 false，并且，只要任意角色返回 false，那么整个判断过程直接返回 false

### 为什么 product 也要忽略旧记忆？【已解决】

metagpt这样设定的，作为项目起始角色，但是，增量开发中或许会设置为false

#### Architect

接下我们进入到 Architect 的执行流程中，Architect 启动依赖于上文中给到的 PRD

依旧是 observe ，这里的 news 就是 PRD 了

> architect 是不会忽略旧记忆的，目前，环境中存在3条消息，第一条是人的需求，第二条是PM发的新建文件夹的消息，第三条是PRD，记住第三条还位于各角色的 msg_buffer 中

这里，Architect 的 watch 是

![image-20240315164345534](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315164345534.png)

而消息的cause by 恰好是

![image-20240315164432990](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315164432990.png)

因此 Architect 就顺利读到了这条消息，存储到 rc.news 和 latest_observed_msg 中去

和前文一样，这里的 react 依然是第一个分支

![image-20240315164603502](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315164603502.png)

> set_state=0 是什么意思？
>
> 初步目测是和 set_todo 一起联系

对于 Architect 来说，现在 state = 0，todo就是 **actions【注意这是一个数组】**的第一个元素，也就是 WriteDesign，实际上，许多角色也只完成一个工作，因此 state=0是很常见的

![image-20240315165746899](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315165746899.png)

这里细看一下 think，因为 PM 的 think 是被重写的，这里我们看一下基类 role 的 think

![image-20240315170056708](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315170056708.png)

初步的意思是，如果只有一个动作，那么就不需要下面的 prompt 大模型来决定后续动作的操作，先停在这里，如果有 prompt 的操作，我们再继续看，反正对于 Architect 来说，这一步直接就是 return了

既然 think 结束，那就就是 act 阶段，同样的，角色的 act 实际上就是角色有的 action 的 run，这里就是 Write Design 的 run

![image-20240315170319026](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315170319026.png)

> 这里由于异步函数，又会突然跳到其他角色的执行流中，注意debug控制台的变化

这里会发生一些对文件的操作，由于我们是初次生成，因此无需关心这些步骤，只要关心 prompt 的操作就好

出错了，重新debug，正好把这一部分补充一下

**prd** 是从filename中读取出来的，filename是一个暂时的名字，例如20240321等临时名称

**old_system_design_doc** 由于我们是第一次生成项目，因此为 None，所以进入if分支中，需要新建一个系统需求设计

![image-20240315231511103](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315231511103.png)

![image-20240315170710611](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315170710611.png)

上图中的 new_system_design 方法就是向大模型提问的方法

提问的方式还是构造prompt，然后执行 fill 方法

这里的 fill 参数很简单，一个是 prd，一个是大模型

![image-20240315231757908](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315231757908.png)

这里点的又快了，没看到 prompt，直接写个 print 好了

> 这里prompt的content有三部分，一部分是 prd 原文，另一部分是 metagpt提供的 design 的模板实例（以snake游戏为例），最后一部分是限制，比如使用同样的语言，告诉大模型要遵循格式等

![image-20240315170823284](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315170823284.png)

![image-20240315170839773](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315170839773.png)

![image-20240315232525312](C:/Users/25929/AppData/Roaming/Typora/typora-user-images/image-20240315232525312.png)最后prompt大模型时，这个 system_msg 没传，因此使用预定义的角色 prompt：

![image-20240315232636180](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315232636180.png)

最后给 gpt 的 message 分为两部分，如前文一样，一个是 system，一个是user，就是我们自己的需求

![image-20240315232810277](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315232810277.png)

完成后就生成了系统设计文档（还是原来的需求文档，但是是可以被mermaid读取的格式） 

然后是一堆调用 mermaid 保存文件的过程，这个过程很容易发生一些错误，时有时无非常讨厌

动作的 run 返回后，重新回到角色的 act 中去，构造角色这次执行的消息，准备发给其他角色（这里的流程就很相似了）

![image-20240315171332416](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315171332416.png)

![image-20240315171414103](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315171414103.png)

由于 send_to 还是 all，因此这条消息也会被系统广播给所有人，添加到 msg_buffer 中去

执行结束后，state变为负数，从而 to_do 为 None

> 感觉每一轮中，应该有一部分是根据 to_do 来决定这一轮角色要不要参与，不要就快速的跳过，但还没有发现这一部分的代码

![image-20240315171531119](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315171531119.png)

再往后就是 Project Manager 的流程了

#### Project Manager

往后就挑选值得关注的部分写了，流程依然是 observe - think - act 的模式

![image-20240315234609518](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315234609518.png)

输入是上一步的 system_design，内容如下：

![image-20240315234723151](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315234723151.png)

> 结合 WriteDesign 来看，每个动作的 prompt 大致可分为
>
> 1. 相关上下文，通常是前一个自己监听的角色的输出
>
>    ![image-20240315235501957](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315235501957.png)
>
> 2. 例子，例子的格式就是自己想要得到的输出的格式，在这里自然就是 task list 的格式
>
>    ![image-20240315235443899](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315235443899.png)
>
> 3. 输出格式里每一个节点的含义
>
>    ![image-20240315235434867](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315235434867.png)
>
> 4. 限制和要求，告诉大模型遵循的规则，并且按照节点执行，这一步好像是所有动作都通用的
>
>    ![](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240315235510864.png)

#### Engineer

最后的最后，让我们看 Engineer 

![image-20240318000457215](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240318000457215.png)

一系列的操作来找到工作目录

![image-20240318001201043](C:/Users/25929/AppData/Roaming/Typora/typora-user-images/image-20240318001201043.png)

这里有3条分支 对应不同的任务，第一个是增量开发，第二个是正常代码，第三个是总结？这里就进入第二个

![image-20240318003007929](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240318003007929.png)

这里有很多的，文件路径的操作

![image-20240318005539017](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240318005539017.png)

这里是上一步列出的，需要实现的文件

所以即使是多步骤的think，也没有 prompt 大模型

这里依然是让大模型执行角色扮演

![image-20240318005910677](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240318005910677.png)

与前文类似，prompt 可以分为如下部分：

1. Architect 写的 design

2. Product Manager 写的 task
3. 模板
4. 限制

有多少个文件就有多少个 writing的过程

![image-20240318140603528](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240318140603528.png)

从这里可以看到，在写完第一个 game.py 文件后，写 main.py 时，还是重新让大模型角色扮演，参考的 context 是一模一样的，但是，关键的是上下文不包含大模型之前生成的代码

> 因此可以合理的推测大模型并没有保存上下文记忆，每次我们进行prompt都是一次新的prompt

![image-20240318140902764](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240318140902764.png)

这里可以注意到，以前的角色执行完毕后，发送的消息都是包含内容（指prd，design，tasks），但是 Engineer 执行完毕后，只是返回文件名，不包含代码

### 此轮结束后，所有角色就变为了idle，检查情况后发现这一步的广播有特殊情况【已解决】

![image-20240318144246710](https://gitee.com/fancy_R/picgo-picture/raw/master/img/image-20240318144246710.png)

send_to 不再是 all 了，因此这里 Engineer 执行完 WriteCode 后只发给了自己，其他人自然 idle 就变为了 false



最后，5轮次结束，程序执行完毕

> 后续还有测试等步骤，拓展功能的执行列表不再细细说明
>
> 打通 metagpt 流程然后探索执行新任务的方法才是关键
>
> 之后开始看新的 metagpt 发的论文

