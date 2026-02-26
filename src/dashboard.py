import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import json
import os

# --- 1. 基础配置 ---
st.set_page_config(
    page_title="Resilient ETL Workbench",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API_URL = "http://127.0.0.1:8000"
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- 2. 状态管理 ---
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'upload'
if 'current_detail_id' not in st.session_state:
    st.session_state.current_detail_id = None

# --- 3. 侧边栏：历史记录 ---
with st.sidebar:
    st.header("🗃️ 历史记录")
    if st.button("➕ 新建提取任务", use_container_width=True):
        st.session_state.view_mode = 'upload'
        st.rerun()

    st.divider()

    # 获取历史列表
    try:
        resp = requests.get(f"{API_URL}/history")
        if resp.status_code == 200:
            history_list = resp.json()
            if not history_list:
                st.caption("暂无记录")

            for item in history_list:
                dt = datetime.fromisoformat(item['created_at'])
                time_str = dt.strftime("%m-%d %H:%M")

                # 状态图标逻辑
                if item['status'] == 'success':
                    icon = "✅"
                elif item['status'] == 'reviewed':  # 新增状态
                    icon = "👮"
                elif item['status'] == 'review_needed':
                    icon = "⚠️"
                else:
                    icon = "❌"

                btn_label = f"{icon} {item['filename'][:15]}.. ({time_str})"

                if st.button(btn_label, key=f"hist_{item['id']}", use_container_width=True):
                    st.session_state.view_mode = 'detail'
                    st.session_state.current_detail_id = item['id']
                    st.rerun()
        else:
            st.error("无法连接数据库")
    except Exception as e:
        st.error(f"连接失败: {e}")

    st.divider()

    # 导出功能区
    with st.expander("📊 数据导出"):
        export_type = st.selectbox("选择导出类型", ["全部记录", "仅发票", "仅合同"])

        if st.button("📥 生成 CSV 报表"):
            try:
                # 获取所有历史记录 (建议增加一个无分页的全量接口，或者循环分页拉取)
                # 简单起见，我们先拉取前 100 条
                all_resp = requests.get(f"{API_URL}/history?limit=100")
                if all_resp.status_code == 200:
                    raw_data = all_resp.json()

                    # 数据清洗与展平
                    export_data = []
                    for item in raw_data:
                        # 过滤类型
                        if export_type == "仅发票" and item.get('doc_type') != 'invoice': continue
                        if export_type == "仅合同" and item.get('doc_type') != 'contract': continue

                        # 基础字段
                        row = {
                            "ID": item['id'],
                            "文件名": item['filename'],
                            "类型": item.get('doc_type'),
                            "状态": item['status'],
                            "置信度": item.get('confidence'),
                            "创建时间": item['created_at']
                        }

                        # 尝试获取详细数据 (列表接口可能不返回 huge JSON，需要单独 fetch 或者后端支持)
                        # 这里假设列表接口已经返回了简单的 data 摘要，或者我们前端去 fetch detail
                        # 优化方案：后端增加一个 /export 接口专门做这个。
                        # 临时方案：前端循环 fetch detail (慢，但能用)

                        # 更优方案：修改后端 /history 接口，让它返回 data 字段 (如果数据不大)
                        # 或者，我们直接在列表页显示 data 的关键字段（如金额）

                        # 假设我们后端列表页没返回 data，那我们得请求详情
                        try:
                            detail = requests.get(f"{API_URL}/history/{item['id']}").json()
                            data = detail.get('data') or {}

                            if detail.get('doc_type') == 'invoice':
                                row['发票号'] = data.get('invoice_number')
                                row['金额'] = data.get('total_amount')
                                row['日期'] = data.get('date')
                                row['供应商'] = data.get('vendor_name')
                            elif detail.get('doc_type') == 'contract':
                                row['合同标题'] = data.get('title')
                                row['甲方'] = data.get('party_a')
                                row['乙方'] = data.get('party_b')
                                row['总金额'] = data.get('total_value')
                        except:
                            pass

                        export_data.append(row)

                    if export_data:
                        df = pd.DataFrame(export_data)
                        csv = df.to_csv(index=False).encode('utf-8-sig')  # 解决中文乱码

                        st.download_button(
                            label="点击下载 CSV",
                            data=csv,
                            file_name=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("没有符合条件的数据")
                else:
                    st.error("获取数据失败")
            except Exception as e:
                st.error(f"导出失败: {e}")


    st.divider()
    with st.expander("🗑️ 危险操作"):
        if st.button("🔥 清空所有历史", type="primary"):
            requests.delete(f"{API_URL}/history")
            st.session_state.view_mode = 'upload'
            st.rerun()

# --- 4. 主界面逻辑 ---

# ==========================================
# 模式 A: 详情编辑模式 (Human-in-the-loop 核心)
# ==========================================
if st.session_state.view_mode == 'detail' and st.session_state.current_detail_id:
    try:
        # 获取详情
        detail_resp = requests.get(f"{API_URL}/history/{st.session_state.current_detail_id}")
        if detail_resp.status_code == 200:
            detail = detail_resp.json()
            doc_type = detail.get('doc_type')
            data = detail.get('data') or {}

            # --- 顶部导航 ---
            c_back, c_del = st.columns([8, 1])
            if c_back.button("⬅️ 返回"):
                st.session_state.view_mode = 'upload'
                st.rerun()
            if c_del.button("🗑️ 删除"):
                requests.delete(f"{API_URL}/history/{detail['id']}")
                st.session_state.view_mode = 'upload'
                st.rerun()

            st.title(f"📝 审核: {detail['filename']}")

            # 状态横幅
            status = detail['status']
            if status == 'success':
                st.success(f"AI 自动提取成功 (置信度: {detail['confidence']})")
            elif status == 'reviewed':
                st.info(f"👮 人工已复核修正")
            elif status == 'review_needed':
                st.warning(f"⚠️ 置信度低 ({detail['confidence']})，请人工修正数据")
            else:
                st.error(f"❌ 提取失败: {detail.get('error_message')}")

            st.divider()

            # --- 编辑表单区域 ---
            with st.form("edit_form"):
                st.subheader("核心数据修订")

                # 根据文档类型渲染不同的输入框
                new_data = data.copy()  # 复制一份用于修改

                # 初始化变量，防止 UnboundLocalError
                amount_str = None
                val_str = None

                if doc_type == 'invoice':
                    c1, c2, c3 = st.columns(3)
                    new_data['invoice_number'] = c1.text_input("发票号码", value=data.get('invoice_number', ''))
                    new_data['date'] = c2.text_input("开票日期", value=data.get('date', ''))

                    # 金额需要转字符串显示，保存时转回 float
                    amount_str = c3.text_input("总金额", value=str(data.get('total_amount', 0.0)))

                    new_data['vendor_name'] = st.text_input("供应商名称", value=data.get('vendor_name', ''))

                    st.caption("注：商品明细行暂不支持编辑，请直接在下方 JSON 中修正")

                elif doc_type == 'contract':
                    new_data['title'] = st.text_input("合同标题", value=data.get('title', ''))

                    c1, c2 = st.columns(2)
                    new_data['party_a'] = c1.text_input("甲方", value=data.get('party_a', ''))
                    new_data['party_b'] = c2.text_input("乙方", value=data.get('party_b', ''))

                    val_str = st.text_input("合同总额", value=str(data.get('total_value', 0.0)))
                    new_data['risk_clauses'] = st.text_area("风险条款摘要", value=data.get('risk_clauses', ''),
                                                            height=100)

                    # 尝试保存金额
                    try:
                        if doc_type == 'invoice':
                            new_data['total_amount'] = float(amount_str)
                        elif doc_type == 'contract':
                            new_data['total_value'] = float(val_str)
                    except:
                        st.error("金额格式错误，请输入数字")

                else:
                    st.info("未知文档类型，请直接编辑 JSON")

                # 通用 JSON 编辑器 (兜底)
                with st.expander("🔧 高级编辑 (直接修改 JSON)", expanded=(doc_type not in ['invoice', 'contract'])):
                    json_str = st.text_area("JSON Data", value=json.dumps(new_data, indent=2, ensure_ascii=False),
                                            height=300)
                    try:
                        final_json = json.loads(json_str)
                    except:
                        st.error("JSON 格式错误")
                        final_json = new_data

                # 提交按钮
                submitted = st.form_submit_button("💾 保存修正并标记为通过", type="primary")

                if submitted:
                    # 调用 PATCH 接口
                    try:
                        # 优先使用 Form 里的字段，如果用了 JSON 编辑器则用 JSON 的
                        payload = {
                            "data": final_json,
                            "status": "reviewed"
                        }
                        patch_resp = requests.patch(f"{API_URL}/history/{detail['id']}", json=payload)

                        if patch_resp.status_code == 200:
                            st.balloons()
                            st.success("保存成功！")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"保存失败: {patch_resp.text}")
                    except Exception as e:
                        st.error(f"发送请求失败: {e}")

        else:
            st.error("记录加载失败")
            if st.button("返回"):
                st.session_state.view_mode = 'upload'
                st.rerun()

    except Exception as e:
        st.error(f"详情页错误: {e}")


# ==========================================
# 模式 B: 上传模式 (首页)
# ==========================================
else:
    st.markdown("""
        <div style="text-align: center; margin-top: 50px;">
            <h1>⚡ Resilient Doc Parser</h1>
            <p>基于本地大模型与 OCR 的智能文档流水线</p>
        </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader("拖拽文件到此处 (PDF/Word/Image)", type=["pdf", "docx", "png", "jpg", "md"], accept_multiple_files=True)

    if uploaded_files:
        if st.button(f"🚀 开始批量提取 ({len(uploaded_files)} 个文件)", type="primary", use_container_width=True):

            progress_bar = st.progress(0)
            status_text = st.empty()
            success_count = 0
            fail_count = 0

            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"正在提交: {uploaded_file.name} ({i + 1}/{len(uploaded_files)})...")

                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    # 依然调用原来的单文件接口，循环调用
                    response = requests.post(f"{API_URL}/extract", files=files)

                    if response.status_code == 200:
                        success_count += 1
                    else:
                        fail_count += 1
                        st.error(f"{uploaded_file.name} 提交失败")

                except Exception as e:
                    fail_count += 1
                    st.error(f"{uploaded_file.name} 连接错误: {e}")

                # 更新进度条
                progress_bar.progress((i + 1) / len(uploaded_files))

            status_text.success(f"🎉 提交完成！成功: {success_count}, 失败: {fail_count}")
            time.sleep(1)

            if success_count > 0:
                st.info("任务已在后台排队处理，请前往历史记录查看进度。")
                time.sleep(2)
                # 自动跳转到历史列表页（这里假设你有一个列表页模式，或者刷新后侧边栏可见）
                st.rerun()