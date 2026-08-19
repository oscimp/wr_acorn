close all
clear all
N=400;  % assumes 1000 samples/s => update for different sampling rate
        % tested with a tuning word of 5 (3 mHz offset)

% CFAR: noise is not AWGN so CFAR threshold seems not valid
pfa=1e-6;  % Probability of False Alarm Rate
T=sqrt(2)*erfinv(1-2*pfa) % T=norminv(1-pfa); should be *sqrt(2/N)
aff=1

dirlist=dir('*tim');
for dirnum=1:length(dirlist)
  filename=dirlist(dirnum).name
  fid = fopen(filename, 'r');
  if fid == -1
    error('Cannot open file');
  end
 
  l=1; 
  while true
    line = fgetl(fid);
    if ~isempty(strfind(line, 'TIC '))
      break;
    end
    l=l+1;
  end
  val=str2num(line(4:end));
  x=dlmread(filename,'',[l, 0, l+val-1, 1] ); % l = starting line ; val = record length
  x=x-mean(x(1:N));
  if (aff==1) 
     figure;subplot(212);plot(x(1:20000)*1e9)
  end
  n=std(x(N:N*2));
  init=find(conv(x,ones(1,N)/N)(N/2:end-N/2)>T*n);init=init(1)-N % first step
  inittmp=find(x(1:5*N)>T*n); %
  if (aff==1)
     hold on;plot([init:init+2000],x(init:init+2000)*1e9,'r');
     axis([init-1000 init+2000 (x(init-1000)-n)*1e9 (x(init+1000)+n)*1e9])
  end
  x=x(init:end);
  dx=diff(x);
  k=find(dx>T*n);  % indices
  dk=diff(k);
  kk=find(dk>10);
  mean(dk(kk))
  timestep=median(dk(kk))
  oldinit=init;
  x=x-mean(x(1:100));
  init=find(x(1:5*timestep)>T*n); %
  x=x(init(1)-floor(timestep/2):end);
  if (aff==1)
     hold on;plot(oldinit+[1:2000]+init(1)-1-timestep/2,x(1:2000)*1e9,'g');
  end
  step=zeros(ceil(length(x)/timestep),1);
  p=1;
  m=1;
  dt1=5;  % transition width
  timestep_over_2=round(timestep/2);
  do   
      val=x(m:m+timestep-1);
      val1=mean(val(1:timestep_over_2-dt1));
      val2=mean(val(end-timestep_over_2+dt1:end));
      position=find(val>(val1+val2)/2);position=position(1);
      m=m+timestep+(position-timestep_over_2);
      step(p)=val2-val1;
      p=p+1;
  until m>(length(x)-timestep);
  k=find(step>0);
  step=step(k);
  step=step(1:floor(length(step)/112)*112);
  step=reshape(step,112,length(step)/112);
  if (dirnum==3)
     solution=step;
  end
  if (dirnum>3)
     solution=[solution step];
  end
  if (aff==1)
    subplot(211);plot(step);title(strrep(strrep(filename,'_',' '),'.tim',''))
  end
end
figure
solution=solution*1e9;
subplot(211);plot(solution);ylabel('delay (ns)')
std(solution')
subplot(212)
plot(std(solution'));xlabel('position (no unit)');ylabel('std (ns)')
ss=mean(solution')'
ss=ss*112/sum(ss);  % normalize (112 values, mean value is 1)
save -text solution.txt ss
printf("edit solution.txt and remove Octave header\n");
