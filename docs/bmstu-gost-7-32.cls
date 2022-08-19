\NeedsTeXFormat{LaTeX2e}

\ProvidesClass{bmstu-gost-7-32}[202/02/25 BMSTU GOST 7.32-2017]

\LoadClass[a4paper, 14pt]{extreport}

\RequirePackage[T2A]{fontenc}
\RequirePackage[utf8]{inputenc}
\RequirePackage[main=russian, english]{babel}

\RequirePackage{microtype}
\sloppy

\RequirePackage[unicode, hidelinks]{hyperref}

\RequirePackage{bmstu-gost-7-32-p50-requirements-for-the-structural-elements-of-the-report}
\RequirePackage{bmstu-gost-7-32-p60-report-formatting-rules}

%% for title-page
\RequirePackage{wrapfig}
%%
\makeatletter
\def\vhrulefill#1{\leavevmode\leaders\hrule\@height#1\hfill\kern\z@}
\makeatother


%% for listings
\RequirePackage{algorithm}
\RequirePackage{algpseudocode}
%%
\renewcommand{\listalgorithmname}{Список алгоритмов}
\floatname{algorithm}{Алгоритм}
\algrenewcommand\algorithmicwhile{\textbf{До тех пор, пока}}
\algrenewcommand\algorithmicdo{\textbf{выполнять}}
\algrenewcommand\algorithmicrepeat{\textbf{Повторять}}
\algrenewcommand\algorithmicuntil{\textbf{Пока выполняется}}
\algrenewcommand\algorithmicend{\textbf{Конец}}
\algrenewcommand\algorithmicif{\textbf{Если}}
\algrenewcommand\algorithmicelse{\textbf{иначе}}
\algrenewcommand\algorithmicthen{\textbf{тогда}}
\algrenewcommand\algorithmicfor{\textbf{Цикл}}
\algrenewcommand\algorithmicforall{\textbf{Для всех}}
\algrenewcommand\algorithmicfunction{\textbf{Функция}}
\algrenewcommand\algorithmicprocedure{\textbf{Процедура}}
\algrenewcommand\algorithmicloop{\textbf{Зациклить}}
\algrenewcommand\algorithmicrequire{\textbf{Условия:}}
\algrenewcommand\algorithmicensure{\textbf{Обеспечивающие условия:}}
\algrenewcommand\algorithmicreturn{\textbf{Возвратить}}
\algrenewtext{EndWhile}{\textbf{Конец цикла}}
\algrenewtext{EndLoop}{\textbf{Конец зацикливания}}
\algrenewtext{EndFor}{\textbf{Конец цикла}}
\algrenewtext{EndFunction}{\textbf{Конец функции}}
\algrenewtext{EndProcedure}{\textbf{Конец процедуры}}
\algrenewtext{EndIf}{\textbf{Конец условия}}
\algrenewtext{EndFor}{\textbf{Конец цикла}}
\algrenewtext{BeginAlgorithm}{\textbf{Начало алгоритма}}
\algrenewtext{EndAlgorithm}{\textbf{Конец алгоритма}}
\algrenewtext{BeginBlock}{\textbf{Начало блока. }}
\algrenewtext{EndBlock}{\textbf{Конец блока}}
\algrenewtext{ElsIf}{\textbf{иначе если }}
%%
\RequirePackage{listings}
\RequirePackage{listingsutf8}
\RequirePackage{xcolor}
\lstset{
	basicstyle=\ttfamily,
	breakatwhitespace=true,
	breaklines=true,
	commentstyle=\color{gray},
	frame=single,
	inputencoding=utf8/koi8-r,
	keywordstyle=\color{blue}\bfseries,
	showstringspaces=false,
	stringstyle=\color{red},
	tabsize=8,
	xleftmargin=3pt,
	xrightmargin=3pt,
}
%%
\newcommand{\code}[1]{\texttt{#1}}

%% reduce indent in contents
%% https://tex.stackexchange.com/questions/409569/change-indent-in-standard-table-of-content-not-tocloft
\RequirePackage{etoolbox}
\makeatletter
% \patchcmd{<cmd>}{<search>}{<replace>}{<success>}{<failure>}
\patchcmd{\l@section}{1.5em}{1em}{}{}
\patchcmd{\l@subsection}{3.8em}{2em}{}{}
\patchcmd{\l@subsubsection}{7.0em}{3em}{}{}
\makeatother
