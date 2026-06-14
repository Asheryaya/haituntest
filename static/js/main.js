// 海豚计划四期人才测评系统 - 主JavaScript文件

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 自动隐藏flash消息
    setTimeout(function() {
        var flashContainer = document.querySelector('.flash-messages');
        if (flashContainer) {
            var flashMessages = flashContainer.querySelectorAll('.flash-message');
            flashMessages.forEach(function(msg) {
                msg.style.opacity = '0';
                msg.style.transform = 'translateX(100%)';
            });
            setTimeout(function() {
                flashContainer.remove();
            }, 300);
        }
    }, 3000);

    // 选项点击高亮
    var optionItems = document.querySelectorAll('.option-item');
    optionItems.forEach(function(item) {
        item.addEventListener('click', function() {
            var radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                // 移除同组其他选项的选中样式
                var siblings = this.parentElement.querySelectorAll('.option-item');
                siblings.forEach(function(sibling) {
                    sibling.style.borderColor = 'transparent';
                    sibling.style.backgroundColor = '';
                });
                // 添加当前选项的选中样式
                this.style.borderColor = 'var(--primary-color)';
                this.style.backgroundColor = '#E8F0FE';
            }
        });

        // 初始化已选中的选项
        var radio = item.querySelector('input[type="radio"]');
        if (radio && radio.checked) {
            item.style.borderColor = 'var(--primary-color)';
            item.style.backgroundColor = '#E8F0FE';
        }
    });

    // DISC结果图表动画
    var discBars = document.querySelectorAll('.disc-bar .bar');
    discBars.forEach(function(bar) {
        var height = bar.style.height;
        bar.style.height = '0';
        setTimeout(function() {
            bar.style.height = height;
        }, 100);
    });

    // 表格行悬停效果
    var tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(function(row) {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'var(--light-bg)';
        });
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
});

// 确认删除
function confirmDelete(userName) {
    return confirm('确定要删除用户 ' + userName + ' 吗？此操作不可恢复。');
}

// 导出数据
function exportData(type) {
    window.location.href = '/admin/export/' + type;
}
