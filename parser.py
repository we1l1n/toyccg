# -*- coding:utf-8 -*-
from lexicon import *
import inspect
import re


"""
#-- Penn Part of Speech Tags
CC:等位接続詞
CD:数字
DT:限定詞
EX:there構文
FW:外国語
IN:前置詞/従位接続詞
JJ:形容詞/Adjective
JJR:形容詞(比較級)
JJS:形容詞(最上級)
MD:助動詞
NN:名詞(単数形)
NNP:固有名詞(単数形)
NNPS:固有名詞(複数形)
NNS:名詞(複数形)
PDT:限定詞前置語
POS:所有格
PRP:人称代名詞
PRP$:所有代名詞
RB:副詞/Adverb
RBR:副詞(比較級)
RBS:副詞(最上級)
RP:副助詞/Particle
SYM:記号
TO:to
UH:間投詞
UNC:未分類
VB:動詞(基本形)
VBD:動詞(過去形)
VBG:動詞(現在分詞)
VBN:動詞(過去分詞)
VBP:動詞(非三単現)
VBZ:動詞(三単現)
WDT:関係代名詞
WP:疑問代名詞
WP$:疑問代名詞(所有格)
WRB:疑問副詞

"""


BwdApp = Symbol("\\")
FwdApp = Symbol("/")
FORALL = Symbol("forall")


@threadsafe_generator
def mk_gensym():
    sym_id = 0
    while True:
        ret = Symbol("_{0}".format(sym_id))
        yield ret
        sym_id += 1


gensym = mk_gensym()


def subst_single(term , theta):
    if type(term)!=list:
        if term.value() in theta:
            return theta[term.value()]
        else:
            return term
    else:
        return [subst_single(t,theta) for t in term]


def unify(eqlist , vars):
    def recursive(var , term):
       if type(term)!=list:
          return (var==term.value())
       else:
          for t0 in term:
              if recursive(var,t0):
                   return True
       return False
    def subst_multi(eqs , theta):
       ret = []
       for (Lexp,Rexp) in eqs:
           ret.append( (subst_single(Lexp,theta) , subst_single(Rexp,theta)) )
       return ret
    def aux(lt , rt):
       ret = {}
       if type(lt)!=list and type(rt)!=list:
           if not (lt in vars) and not (rt in vars):
              if not(lt==rt):
                 return None
           elif (lt in vars) and not (rt in vars):
              ret[lt.value()] = rt
           elif not (lt in vars) and (rt in vars):
              ret[rt.value()] = lt
           elif (lt in vars) and (rt in vars) and not(lt==rt):
              ret[lt.value()] = rt
       elif type(lt)!=list and type(rt)==list:
           if not (lt in vars):
              return None
           else:
              ret[lt.value()] = rt
       elif type(lt)==list and type(rt)!=list:
           if not (rt in vars):
              return None
           else:
              ret[rt.value()] = lt
       else:
           assert(len(lt)==3),lt
           assert(len(rt)==3),rt
           if not(lt[0]==rt[0]):
              return None
           else:
              ret = solve([(lt[1],rt[1]) , (lt[2],rt[2])])
       return ret
    def solve(eqs):
       theta = {}
       for (Lexp,Rexp) in eqs:
           if type(Lexp)==list and type(Rexp)==list:
              if not (Lexp[0]==Rexp[0]):
                  return None
              theta1 = aux(subst_single(Lexp[1],theta) , subst_single(Rexp[1],theta))
              if theta1==None:return None
              for (k,v) in theta1.iteritems():
                  if recursive(k,v):return None
                  theta[k] = v
              theta2 = aux(subst_single(Lexp[2],theta) , subst_single(Rexp[2],theta))
              if theta2==None:return None
              for (k,v) in theta2.iteritems():
                  if recursive(k,v):return None
                  theta[k] = v
           else:
              theta1 = aux(subst_single(Lexp , theta) , subst_single(Rexp,theta))
              if theta1==None:return None
              for (k,v) in theta1.iteritems():
                  if recursive(k,v):return None
                  theta[k] = v
       return theta
    ret = {}
    eqs = subst_multi(eqlist , ret)
    while True:
       theta = solve(subst_multi(eqlist , ret))
       if theta==None:return None
       if len(theta)==0:break
       for k,v in ret.iteritems():
           ret[k] = subst_single(v , theta)
       for k,v in theta.iteritems():
           ret[k] = v
       _eqs = subst_multi(eqlist , ret)
       if _eqs==eqs:break
    return ret



def term_eq(t1 , t2):
    if type(t1)!=type(t2):
        return False
    elif type(t1)!=list and type(t2)!=list:
        return (t1==t2)
    elif type(t1)==list and type(t2)==list:
        if t1[0].value()=="forall" and t2[0].value()=="forall":
            if len(t1[1])!=len(t2[1]):return False
            Nvars = len(t1[1])
            vars = [gensym.next() for _ in range(2*Nvars)]
            Lt = subst_single(t1[2] , dict(zip([c.value() for c in t1[1]] , vars[:Nvars])))
            Rt = subst_single(t2[2] , dict(zip([c.value() for c in t2[1]] , vars[Nvars:])))
            try:
                vmap = unify([(Lt,Rt)] , vars)
            except:
                assert(False),(t1,t2,vars)
            if vmap==None:return False
            for (k,v) in vmap.iteritems():
                if type(v)==list:return False
                elif not v.value().startswith("_"):return False
            return True
        else:
            return (t1==t2)





def polymorphic(t):
    def _polymorphic(t):
       if type(t)!=list:
          return False
       for t0 in t:
          if type(t0)!=list and t0.value()=="forall":
              return True
          elif type(t0)==list and _polymorphic(t0):
              return True
    if type(t)!=list:
        return False
    else:
        return any([_polymorphic(t0) for t0 in t])


def findvars(term , vars):
    ret = []
    if type(term)!=list:
        if term in vars:
            ret.append(term)
    else:
        ret = sum([findvars(t,vars) for t in term],[])
    return list(set(ret))


#-- right I* combinator (X/Y Y => X)
def RApp(lt , rt):
    if type(lt)!=list and lt.value()=="CONJ":
        return [BwdApp , rt, rt]
    if type(lt)==list and lt[0].value()==FwdApp.value() and term_eq(lt[2],rt):
        return lt[1]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2 = gensym.next(),gensym.next()
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([FwdApp , var1, var2] ,LB) , (var2 , RB)] , oldvars+[var1,var2])
            if mgu!=None and (var1.value() in mgu):
                 NB = mgu[var1.value()]
                 nvars = findvars(NB , oldvars+[var1,var2])
                 if len(nvars)>0:
                      NB = [FORALL , nvars , NB]
                 return NB
    return None


#-- left I* combinator (Y X\Y => X)
def LApp(lt , rt):
    if type(rt)==list and rt[0].value()==BwdApp.value() and term_eq(rt[2],lt):
        return rt[1]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2 = gensym.next(),gensym.next()
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([(var2 , LB) , ([BwdApp , var1, var2] , RB)] , oldvars+[var1,var2])
            if mgu!=None and (var1.value() in mgu):
                 NB = mgu[var1.value()]
                 nvars = findvars(NB , oldvars+[var1,var2])
                 if len(nvars)>0:
                      NB = [FORALL , nvars , NB]
                 return NB
    return None


#-- X/Y Y/Z => X/Z
def RB(lt , rt):
    if type(lt)!=list or type(rt)!=list:
        return None
    elif rt[0].value()==FwdApp.value() and lt[0].value()==FwdApp.value() and term_eq(rt[1],lt[2]):
        return [FwdApp,lt[1],rt[2]]
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = gensym.next(),gensym.next(),gensym.next()
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([FwdApp , var1, var2] ,LB) , ([FwdApp , var2, var3] , RB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [FwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None




#-- X/Y Y\Z => X\Z
def RBx(lt , rt):
    if type(lt)!=list or type(rt)!=list:
        return None
    elif rt[0].value()==BwdApp.value() and lt[0].value()==FwdApp.value() and term_eq(rt[1],lt[2]):
        return [BwdApp,lt[1],rt[2]]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = gensym.next(),gensym.next(),gensym.next()
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([FwdApp , var1, var2] ,LB) , ([BwdApp , var2, var3] , RB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [BwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None


#-- Y\Z X\Y => X\Z
def LB(lt , rt):
    if type(lt)!=list or type(rt)!=list:
        return None
    elif rt[0].value()==BwdApp.value() and rt[0].value()==BwdApp.value() and term_eq(lt[1],rt[2]):
        return [BwdApp,rt[1],lt[2]]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = gensym.next(),gensym.next(),gensym.next()
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([BwdApp , var2, var3] ,LB) , ([BwdApp , var1, var2] , RB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [BwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None


#-- Y/Z X\Y ⇒ X/Z
def LBx(lt , rt):
    if type(lt)!=list or type(rt)!=list:
        return None
    elif rt[0].value()==FwdApp.value() and rt[0].value()==BwdApp.value() and term_eq(lt[1],rt[2]):
        return [FwdApp,lt[1],rt[2]]
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = gensym.next(),gensym.next(),gensym.next()
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([FwdApp , var2, var3] ,LB) , ([BwdApp , var1, var2] , RB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [FwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None


#-- (X/Y)/Z Y/Z => X/Z
def RS(lt, rt):
    if type(lt)!=list or type(rt)!=list or type(lt[1])!=list:
        return None
    elif (lt[0],lt[1][0],rt[0])==(FwdApp,FwdApp,FwdApp) and term_eq(lt[1][2] , rt[1]) and term_eq(lt[2] , rt[2]):
        return [FwdApp,lt[1][1],rt[2]]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = gensym.next(),gensym.next(),gensym.next()
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([FwdApp , [FwdApp , var1, var2] ,var3] ,LB) , ([FwdApp , var2, var3] , RB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [FwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None


#-- (X/Y)\Z Y\Z => X\Z
def RSx(lt , rt):
    if type(lt)!=list or type(rt)!=list or type(lt[1])!=list:
        return None
    elif (lt[0],lt[1][0],rt[0])==(BwdApp,FwdApp,BwdApp) and term_eq(lt[1][2] , rt[1]) and term_eq(lt[2] , rt[2]):
        return [BwdApp,lt[1][1],rt[2]]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = gensym.next(),gensym.next(),gensym.next()
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([BwdApp , [FwdApp , var1, var2] ,var3] ,LB) , ([BwdApp , var2, var3] , RB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [BwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None


#-- Y\Z (X\Y)\Z => X\Z
def LS(lt, rt):
    if type(lt)!=list or type(rt)!=list or type(rt[1])!=list:
        return None
    elif (lt[0],rt[1][0],rt[0])==(BwdApp,BwdApp,BwdApp) and term_eq(lt[1] , rt[1][2]) and term_eq(lt[2] , rt[2]):
        return [BwdApp,rt[1][1],lt[2]]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = gensym.next(),gensym.next(),gensym.next()
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([BwdApp , [BwdApp , var1, var2] ,var3] ,RB) , ([BwdApp , var2, var3] , LB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [BwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None



#-- Y/Z (X\Y)/Z => X/Z
def LSx(lt, rt):
    if type(lt)!=list or type(rt)!=list or type(rt[1])!=list:
        return None
    elif (lt[0],rt[1][0],rt[0])==(FwdApp,BwdApp,FwdApp) and term_eq(lt[1] , rt[1][2]) and term_eq(lt[2] , rt[2]):
        return [FwdApp,rt[1][1],lt[2]]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = gensym.next(),gensym.next(),gensym.next()
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([FwdApp , [BwdApp , var1, var2] ,var3] ,RB) , ([FwdApp , var2, var3] , LB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [FwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None


#-- X => forall a.a/(a\X)
def RT(t):
   if type(t)!=list and t.value()=="NP":
      var = gensym.next()
      return [FORALL , [var] , [FwdApp , var , [BwdApp,var,t]]]
   return None


#-- X => forall.a\(a/X)
def LT(t):
   if (type(t)!=list and t.value() in ["NP","PP","S"]) or t==[BwdApp,Symbol("S"),Symbol("NP")]:
      var = gensym.next()
      return [FORALL , [var] , [BwdApp , var , [FwdApp,var,t]]]
   return None




combinators = [LApp,RApp,LB,RB,LBx,RBx,LS,RS,LSx,RSx,LT,RT]
def CCGChart(tokens,lexicon):
   chart = {}
   N = len(tokens)
   for n,tok in enumerate( tokens ):
      chart[(n,n)] = [(c,tuple()) for c in lexicon.get(tok , [])]
      #-- add type raising
      rest = []
      for cat,path in chart.get((n,n),[]):
         assert(cat!=None),cat
         for f in combinators:
             assert(inspect.isfunction(f))
             if len(inspect.getargspec(f).args)==1:
                 cat2 = f(cat)
                 if cat2!=None:rest.append( (cat2 , path) )
      chart[(n,n)] = chart.get((n,n),[]) + rest
   for width in range(1,N):
      for start in range(0 , N-width):
         for partition in range(0,width):
             left_start = start
             left_end = start + partition
             right_start = left_end + 1
             right_end = start+width
             assert(left_start<=left_end)
             assert(right_start<=right_end)
             assert(left_end<N)
             assert(right_end<N)
             for idx1,(LB,Lpath) in enumerate(chart.get((left_start,left_end),[])):
                 for idx2,(RB,Rpath) in enumerate(chart.get((right_start,right_end),[])):
                    for f in combinators:
                       assert(inspect.isfunction(f))
                       if len(inspect.getargspec(f).args)==2:
                          cat2 = f(LB,RB)
                          if cat2!=None:
                              path = (idx1,idx2,left_end,f.__name__)
                              chart.setdefault( (left_start,right_end) , []).append( (cat2 , path) )
             #-- add type raising
             rest = []
             for idx,(cat,_) in enumerate(chart.get((left_start,right_end),[])):
                 assert(cat!=None),cat
                 for f in combinators:
                    assert(inspect.isfunction(f))
                    if len(inspect.getargspec(f).args)==1:
                       cat2 = f(cat)
                       if cat2!=None:
                            path = (idx,f.__name__)
                            rest.append( (cat2 , path) )
             chart[(left_start ,right_end)] = chart.get((left_start,right_end),[]) + rest
   return chart



class Lexicon(object):
    def __init__(self, filename=None):
        self.static_dics = {}
        if filename!=None:
             for line in open(filename):
                 line = line.strip()
                 if len(line)==0:continue
                 tok,_,cats = line.split('\t')
                 self.static_dics[tok] = [c for c in cats.split(",")]
    def __getitem__(self,tok):
        cats = self.static_dics.get(tok)
        if re.match(r'\d+$',tok):
             cats.append( "NP" )
             cats.append( "NP/N[pl]" )
             cats.append( "NP/N" )
        return [lexparse(c) for c in cats]
    def __setitem__(self,tok,cats):
        self.static_dics[tok] = cats
    def get(self,_tok,defval):
        try:
           return self.__getitem__(_tok)
        except:
           pass
        try:
           return self.__getitem__(_tok.lower())
        except:
           return [lexparse(c) for c in defval]



terminators = ["ROOT","S","S[q]","S[wq]"]
def testrun(tokens,lexicon):
   def _catname(t):
       if type(t)!=list:
           return t.value()
       elif t[0]==FwdApp:
           return "({0}/{1})".format(_catname(t[1]) , _catname(t[2]))
       elif t[0]==BwdApp:
           return "({0}\\{1})".format(_catname(t[1]) , _catname(t[2]))
       elif t[0]==FORALL:
           return "(\\{0}->{1})".format(",".join([x.value() for x in t[1]]) , _catname(t[2]))
       else:
           assert(False),t
   def catname(t):
       tmp = _catname(t)
       if tmp[0]=="(" and tmp[-1]==")":
           return tmp[1:-1]
       else:
           return tmp
   def decode(left_start , right_end , path , chart):
       if len(path)==0:
          assert(left_start==right_end)
          return tokens[left_start]
       elif len(path)==2:
          idx = path[0]
          cat1,path1 = chart[(left_start,right_end)][idx]
          return decode(left_start,right_end , path1 , chart)
       else:
          assert(len(path)==4),path
          idx1,idx2,left_end,_ = path
          right_start = left_end+1
          cat1,path1 = chart[(left_start,left_end)][idx1]
          cat2,path2 = chart[(right_start,right_end)][idx2]
          return ((catname(cat1),decode(left_start,left_end , path1 , chart)) , (catname(cat2),decode(right_start,right_end , path2, chart)))
   chart = CCGChart(tokens,lexicon)
   print("test run : tokens={0}".format(str(tokens)))
   for (topcat,path) in chart.get((0,len(tokens)-1) ,[]):
       if type(topcat)!=list and topcat.value() in terminators:
           print( decode(0 , len(tokens)-1 , path , chart) )
   print("")


import os
if __name__=="__main__":
   lexicon = {"I":[lexparse("NP")] , "am":[lexparse("(S\\NP)/NP")] , "Mary":[lexparse("NP")]}
   tokens = "I am Mary".split()
   testrun(tokens , lexicon)
   lexicon = Lexicon()
   lexicon["This"] = ["NP"]
   lexicon["is"] = ["(S\\NP)/NP"]
   lexicon["a"] = ["NP/N"]
   lexicon["pen"] = ["N"]
   testrun("This is a pen".split() , lexicon)
   lexicon = Lexicon(os.path.join(os.path.dirname(os.path.abspath(__file__)) ,"ccglex.en"))
   testrun("I saw a girl with a telescope".split() , lexicon)
   testrun("The boy was there when the sun rose".split() , lexicon)
   testrun("She looks at me".split() , lexicon)
   testrun("He conjectured and might prove completeness".split() , lexicon)
