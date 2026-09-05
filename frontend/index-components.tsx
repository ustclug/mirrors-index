import { useEffect, useRef, useState } from "preact/hooks";
import {
  currentPalette,
  PALETTES,
  selectPalette,
  type Palette,
} from "./palette";
import type { DownloadGroup, IndexDataV1 } from "./types";

export function Header() {
  return (
    <>
      <div id="header">
        <ul id="headlinks">
          <li>
            <a href="/status/" target="_blank">
              Status
            </a>
          </li>
          <li>
            <a href="https://servers.ustclug.org/" target="_blank">
              News
            </a>
          </li>
          <li>
            <a href="/help/" target="_blank">
              Help
            </a>
          </li>
          <li>
            <a href="https://lug.ustc.edu.cn" target="_blank">
              About
            </a>
          </li>
        </ul>
      </div>
      <div id="welcome">
        <div id="intro">
          <h1 id="infinity">Another infinity</h1>
          <h2>Welcome to USTC open source software mirror.</h2>
          <p>
            Brought to you by University of Science and Technology of China and
            USTCLUG.
          </p>
          <br />
        </div>
      </div>
    </>
  );
}

export function DownloadModal({
  kind,
  groups,
  onClose,
}: {
  kind: "os" | "app";
  groups: DownloadGroup[];
  onClose: () => void;
}) {
  const [distro, setDistro] = useState(0);
  const dialog = useRef<HTMLDialogElement>(null);
  const initialFocus = useRef<HTMLButtonElement>(null);
  const selected = groups[distro];
  const app = kind === "app";

  useEffect(() => {
    const previousFocus = document.activeElement;
    dialog.current?.showModal();
    document.body.classList.add("modal-open");
    initialFocus.current?.focus();
    return () => {
      document.body.classList.remove("modal-open");
      if (previousFocus instanceof HTMLElement && previousFocus.isConnected) {
        requestAnimationFrame(() => previousFocus.focus());
      }
    };
  }, []);

  function filename(url: string) {
    const value = url.split("/").pop() || url;
    try {
      return decodeURIComponent(value);
    } catch {
      return value;
    }
  }

  function uncommonArchitecture(name: string) {
    if (name.toLowerCase().includes("android")) return undefined;
    return name.match(/aarch64|ppc64le|arm64/i)?.[0];
  }

  return (
    <dialog
      ref={dialog}
      class={`modal modal-${kind}`}
      aria-labelledby="download-modal-title"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
    >
      <div class="modalcontainer">
        <header class="modalheader">
          <h2 id="download-modal-title">
            {app ? "获取开源软件" : "获取安装镜像"}
          </h2>
          <button
            class="modalclose"
            type="button"
            aria-label="关闭"
            title="关闭"
            onClick={onClose}
          >
            ×
          </button>
        </header>
        <div class="modalbody modalbody-split">
          {groups.length === 0 ? (
            <p class="modalempty-state">
              暂无可用的{app ? "开源软件" : "安装镜像"}下载。
            </p>
          ) : (
            <>
              <nav class="modalnav" aria-label={app ? "开源软件" : "发行版"}>
                <ul>
                  {groups.map((entry, index) => (
                    <li>
                      <button
                        ref={index === 0 ? initialFocus : undefined}
                        type="button"
                        class={index === distro ? "active" : ""}
                        aria-current={index === distro ? "true" : "false"}
                        onClick={() => setDistro(index)}
                      >
                        {entry.distro}
                      </button>
                    </li>
                  ))}
                </ul>
              </nav>
              <section class="modalpanel" aria-labelledby="distro-title">
                <div class="modalpanel-header">
                  <h3 id="distro-title">{selected.distro}</h3>
                  <p class="modalcount">{selected.urls.length} 个文件</p>
                </div>
                {selected.urls.length ? (
                  <ul class="modalfile-list">
                    {selected.urls.map((entry) => {
                      const arch = uncommonArchitecture(entry.name);
                      return (
                        <li class="modalfile">
                          <a
                            href={entry.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={onClose}
                          >
                            <span class="modalfile-name">
                              {entry.name}
                              {arch && (
                                <span class="modalfile-warning">
                                  请确认设备支持 {arch}
                                </span>
                              )}
                            </span>
                            <span class="modalfile-filename">
                              {filename(entry.url)}
                            </span>
                            <span class="modalfile-action">下载</span>
                          </a>
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p class="modalempty">暂无可用文件。</p>
                )}
              </section>
            </>
          )}
        </div>
      </div>
    </dialog>
  );
}

export function Sidebar({
  data,
  open,
}: {
  data: IndexDataV1;
  open: (kind: "os" | "app") => void;
}) {
  const domains = [
    ["//mirrors.ustc.edu.cn/", "mirrors.ustc.edu.cn", "自动解析"],
    ["//ipv4.mirrors.ustc.edu.cn/", "ipv4.mirrors.ustc.edu.cn", "IPv4 线路"],
    ["//ipv6.mirrors.ustc.edu.cn/", "ipv6.mirrors.ustc.edu.cn", "IPv6 线路"],
    [
      "//cernet.mirrors.ustc.edu.cn/",
      "cernet.mirrors.ustc.edu.cn",
      "教育网线路",
    ],
    [
      "//chinanet.mirrors.ustc.edu.cn/",
      "chinanet.mirrors.ustc.edu.cn",
      "电信线路",
    ],
    ["//unicom.mirrors.ustc.edu.cn/", "unicom.mirrors.ustc.edu.cn", "联通线路"],
    ["//cmcc.mirrors.ustc.edu.cn/", "cmcc.mirrors.ustc.edu.cn", "移动线路"],
    ["/help/rsync-guide.html", "rsync.mirrors.ustc.edu.cn", "Rsync 线路"],
  ];
  return (
    <div id="sidebar">
      <div id="mirrorshelp">
        <h3>Mirrors 帮助</h3>
        <p>
          如果您不了解如何配置 Linux 发行版 /
          软件的安装源，这里为您提供了主流发行版的软件源配置帮助：
        </p>
        <a class="btn" href="/help/" target="_blank">
          使用帮助 &gt;
        </a>
        <p>您也可以通过左边的文件列表中相应源的 Help 链接寻求帮助。</p>
      </div>
      <div id="servernews">
        <h3>
          <a href="https://servers.ustclug.org/category/#mirrors">
            镜像站新闻通知
          </a>
        </h3>
        {data.news.length ? (
          data.news.map((record) => (
            <p>
              <a href={record.url}>{record.title}</a>
            </p>
          ))
        ) : (
          <p>新闻服务器出故障了, 正在抢修当中 :(</p>
        )}
      </div>
      <div id="cdimages">
        <h3>获取发行版映像</h3>
        <p>
          这里为您提供各大主流 Linux 发行版的安装镜像 / ISO
          文件，请根据您的发行版及其详细版本进行选择：
        </p>
        <p></p>
        <button class="btn" type="button" onClick={() => open("os")}>
          获取安装镜像 &gt;
        </button>
      </div>
      <div id="ossapps">
        <h3>获取开源软件安装包</h3>
        <p>这里也为您提供常用开源软件的安装包：</p>
        <p></p>
        <button class="btn" type="button" onClick={() => open("app")}>
          获取开源软件 &gt;
        </button>
      </div>
      <div id="mirrorlinks">
        <h3>常用链接</h3>
        <a href="/status" target="_blank">
          系统状态 / Status
        </a>
        <br />
        <a href="https://servers.ustclug.org/" target="_blank">
          LUG 服务器新闻 / News
        </a>
        <br />
        <a href="https://lug.ustc.edu.cn/" target="_blank">
          LUG @ USTC
        </a>
        <br />
        <a href="https://github.com/ustclug/mirrorrequest/" target="_blank">
          新增镜像 / New Mirror
        </a>
        <br />
        <a href="https://github.com/ustclug/discussions/">
          问题跟踪 / Issue Tracker
        </a>
        <br />
        <a href="mailto:lug@ustc.edu.cn">联系我们 / Contact US</a>
        <br />
        <a href="https://mirrors.cernet.edu.cn/list" target="_blank">
          教育网联合镜像站
        </a>
        <br />
      </div>
      <div id="domains">
        <h3>域名选择</h3>
        <table>
          <tbody>
            {domains.map(([url, label, description]) => (
              <tr>
                <td>
                  <a href={url}>{label}</a>
                </td>
                <td>{description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function Footer() {
  const [palette, setPalette] = useState<Palette>(currentPalette);

  function choosePalette(nextPalette: Palette) {
    selectPalette(nextPalette);
    setPalette(nextPalette);
  }

  return (
    <div id="footer">
      <div id="footercontent">
        <div id="footerleft">
          <p>
            中国科学技术大学开源软件镜像由{" "}
            <a href="http://ustcnet.ustc.edu.cn/">
              中国科学技术大学网络信息中心
            </a>{" "}
            提供支持。
          </p>
          <p>
            mirrors.ustc.edu.cn 是 Debian, Ubuntu, Fedora, Archlinux, CentOS
            等多个发行版的官方源。目前是中国大陆高校访问量最大、收录最全的开源软件镜像之一。
          </p>
          <p>
            <a href="https://lug.ustc.edu.cn/">
              中国科学技术大学 Linux 用户协会
            </a>{" "}
            是由中国科学技术大学在校的 GNU/Linux
            爱好者发起并组成的一个全校性群众团体。成立协会的目的在于联合科大的
            GNU/Linux
            使用者，搭建信息交流共享的平台，宣传自由软件的价值，提高自由软件社区文化氛围，推广自由软件在科大校园乃至合肥地区的应用。
          </p>
          <p>
            源代码：
            <a href="https://git.lug.ustc.edu.cn/mirrors/mirrors-index">
              镜像站主页
            </a>{" "}
            <a href="https://github.com/ustclug/yuki">镜像管理器</a>{" "}
            <a href="https://github.com/ustclug/ustcmirror-images">
              镜像同步容器
            </a>
          </p>
        </div>
        <div id="footerright">
          <p>
            <span class="footer-logo">LUG</span>
            <span class="footer-logo footer-logo-light">@USTC</span>
          </p>
          <p class="footer-motto">"life,love,linux"</p>
          <div class="palette-picker" role="group" aria-label="选择配色">
            {PALETTES.map((option) => (
              <button
                key={option.id}
                class="palette-option"
                type="button"
                aria-label={option.name}
                aria-pressed={palette === option.id}
                onClick={() => choosePalette(option.id)}
              >
                <span
                  class={`palette-swatch palette-swatch-${option.id}`}
                  aria-hidden="true"
                />
                <span class="palette-tooltip" role="tooltip">
                  {option.name}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
