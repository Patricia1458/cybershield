from django.core.management.base import BaseCommand

from training.models import TrainingModule, QuizQuestion

MODULES = [
    {
        'title': 'Recognizing Email Phishing Attempts',
        'category': 'phishing',
        'description': 'Learn to spot the warning signs of a phishing email before you click.',
        'content': (
            "Phishing is a type of cyberattack where an attacker impersonates a trusted organization or "
            "person, usually through email, to trick you into revealing sensitive information, clicking a "
            "malicious link, or downloading malware.\n\n"
            "How it works: Attackers craft emails that look like they come from a legitimate source, such as "
            "your bank, employer, or a well-known company. These emails often create a sense of urgency or "
            "fear, pressuring you to act quickly without stopping to verify the request. The email typically "
            "contains a link to a fake website designed to steal your login credentials, or an attachment "
            "containing malware.\n\n"
            "Common examples include: fake 'account suspended' notices asking you to log in urgently, fake "
            "invoices or payment requests from a 'vendor,' emails claiming you've won a prize, and messages "
            "impersonating your company's IT department asking you to 'verify' your password."
        ),
        'scenario': (
            "You receive an email that appears to be from 'IT Support' with the subject line 'Urgent: Your "
            "Account Will Be Suspended.' The email says your company email account has been flagged for "
            "unusual activity and asks you to click a link within 24 hours to verify your identity, or your "
            "account will be permanently locked. The sender's address is it-support@techstart-secure-verify.com."
        ),
        'questions': [
            {
                'question_text': 'What is the biggest red flag in this scenario?',
                'option_a': 'The email uses formal language',
                'option_b': "The sender's domain is not the real company domain",
                'option_c': 'The email has a subject line',
                'option_d': 'The email was sent during work hours',
                'correct_option': 'b',
            },
            {
                'question_text': 'What should you do if you receive an email like this?',
                'option_a': 'Click the link immediately to avoid losing access',
                'option_b': 'Reply to the email asking for more information',
                'option_c': 'Verify by contacting IT directly through a known, separate channel',
                'option_d': 'Forward it to a coworker to check first',
                'correct_option': 'c',
            },
            {
                'question_text': "Why do attackers use urgency ('within 24 hours') in phishing emails?",
                'option_a': 'To comply with email regulations',
                'option_b': 'To pressure you into acting before thinking carefully',
                'option_c': "It's a technical requirement of email servers",
                'option_d': 'It has no real purpose',
                'correct_option': 'b',
            },
            {
                'question_text': 'A legitimate IT department would typically:',
                'option_a': 'Ask you to confirm your password by email',
                'option_b': 'Never contact you about account issues',
                'option_c': 'Direct you to official, verified internal channels rather than urgent email links',
                'option_d': 'Threaten immediate account suspension by email',
                'correct_option': 'c',
            },
            {
                'question_text': 'What does a mismatched sender domain usually indicate?',
                'option_a': 'A spelling mistake by IT',
                'option_b': 'A likely phishing attempt using a lookalike domain',
                'option_c': 'A new official company domain',
                'option_d': 'Nothing significant',
                'correct_option': 'b',
            },
        ],
    },
    {
        'title': 'Spotting Smishing (SMS Phishing) Attacks',
        'category': 'smishing',
        'description': 'Text message scams are increasingly common — learn how to identify them.',
        'content': (
            "Smishing is phishing conducted via SMS text message instead of email. Because text messages feel "
            "more personal and immediate than email, people are often less cautious with them, which attackers "
            "exploit.\n\n"
            "How it works: Attackers send texts impersonating banks, delivery companies, payroll systems, or "
            "government agencies, usually containing a shortened or suspicious link and a false sense of "
            "urgency (a 'failed delivery,' a 'locked account,' or a 'missed payment').\n\n"
            "Common examples: fake delivery notifications asking you to 'reschedule' via a link, fake bank "
            "fraud alerts asking you to 'verify' by clicking, and fake payroll messages about a 'failed direct "
            "deposit.'"
        ),
        'scenario': (
            "You receive a text message that reads: 'TechStart Payroll: Your direct deposit failed. Update "
            "your banking details within 2 hours to avoid a delay in your paycheck: "
            "bit.ly/techstart-payroll-fix'. The message came from an unknown number, not a saved contact."
        ),
        'questions': [
            {
                'question_text': 'What makes this text message suspicious?',
                'option_a': 'It mentions payroll',
                'option_b': 'It uses a shortened, unfamiliar link and creates urgency',
                'option_c': 'It was sent in the morning',
                'option_d': "It's addressed to 'you'",
                'correct_option': 'b',
            },
            {
                'question_text': 'What is a shortened link commonly used for in smishing attacks?',
                'option_a': 'Making links load faster',
                'option_b': 'Hiding the real, potentially malicious destination of a link',
                'option_c': 'Reducing text message character limits only',
                'option_d': "Nothing suspicious, it's standard practice",
                'correct_option': 'b',
            },
            {
                'question_text': 'What should you do if you receive this message?',
                'option_a': "Click the link to check if it's real",
                'option_b': "Reply 'STOP' to unsubscribe",
                'option_c': 'Contact your actual payroll/HR department directly using known contact details',
                'option_d': 'Forward your bank details to confirm',
                'correct_option': 'c',
            },
            {
                'question_text': 'Why are smishing attacks often effective?',
                'option_a': 'People tend to trust text messages more and act on them quickly',
                'option_b': 'Phones cannot receive spam',
                'option_c': 'Text messages are always verified by carriers',
                'option_d': 'They are illegal so people trust them',
                'correct_option': 'a',
            },
            {
                'question_text': 'A legitimate company needing to update your banking details would typically:',
                'option_a': 'Text you a link with a countdown timer',
                'option_b': 'Direct you to log in through their official app or website directly',
                'option_c': 'Ask for your bank PIN over text',
                'option_d': 'Never need to update banking details',
                'correct_option': 'b',
            },
        ],
    },
    {
        'title': 'Defending Against Vishing (Voice Phishing) Calls',
        'category': 'vishing',
        'description': "Phone-based scams can be highly convincing — here's how to protect yourself.",
        'content': (
            "Vishing is phishing conducted over a phone call. Attackers rely on a confident, authoritative "
            "tone and manufactured urgency to pressure victims into revealing sensitive information verbally, "
            "which can feel harder to refuse than ignoring an email or text.\n\n"
            "How it works: Attackers may impersonate your bank's fraud department, a government agency, or "
            "internal IT/HR staff, often using caller ID spoofing to appear legitimate. They typically ask for "
            "account numbers, PINs, one-time passcodes, or remote access to your computer.\n\n"
            "Common examples: fake bank fraud department calls, fake tech support calls claiming your computer "
            "is infected, and fake calls from 'HR' asking you to confirm your bank details for payroll."
        ),
        'scenario': (
            "You receive a phone call from someone claiming to be from your bank's fraud prevention team. The "
            "caller states there has been suspicious activity on your account and asks you to confirm your "
            "full card number and PIN 'to verify your identity and stop the fraudulent transaction "
            "immediately.'"
        ),
        'questions': [
            {
                'question_text': 'What is the major warning sign in this call?',
                'option_a': 'The caller mentioned fraud prevention',
                'option_b': 'A legitimate bank asking for your full PIN over the phone',
                'option_c': 'The call came during business hours',
                'option_d': 'The caller had a professional tone',
                'correct_option': 'b',
            },
            {
                'question_text': 'What should you do if you receive a call like this?',
                'option_a': 'Provide the information quickly to stop the fraud',
                'option_b': 'Hang up and call your bank directly using the number on your card',
                'option_c': 'Ask the caller to email you instead',
                'option_d': 'Give a partial PIN to test them',
                'correct_option': 'b',
            },
            {
                'question_text': "Why do vishing attackers create urgency about 'stopping fraud immediately'?",
                'option_a': 'Banks require immediate verbal confirmation',
                'option_b': 'To prevent you from pausing to verify their legitimacy',
                'option_c': 'It speeds up call center processing',
                'option_d': "It's a standard banking procedure",
                'correct_option': 'b',
            },
            {
                'question_text': 'Which information should you never share over an unsolicited call?',
                'option_a': 'Your name',
                'option_b': 'Your full PIN or card security code',
                'option_c': 'The city you live in',
                'option_d': 'Your job title',
                'correct_option': 'b',
            },
            {
                'question_text': 'A genuine bank fraud department would typically:',
                'option_a': "Ask for your full PIN to 'confirm' your identity",
                'option_b': 'Already have your account details and never need your PIN read aloud',
                'option_c': "Threaten to freeze your account immediately if you don't comply",
                'option_d': 'Call from a blocked or unknown number only',
                'correct_option': 'b',
            },
        ],
    },
    {
        'title': 'Understanding Social Engineering Tactics',
        'category': 'social_engineering',
        'description': 'Learn how attackers manipulate people, not just systems, to gain access.',
        'content': (
            "Social engineering is the psychological manipulation of people into performing actions or "
            "divulging confidential information, rather than breaking through technical security measures. "
            "Attackers exploit human tendencies like trust, fear, curiosity, and the desire to be helpful.\n\n"
            "Common techniques include: pretexting (inventing a fabricated scenario to obtain information), "
            "baiting (leaving infected USB drives in visible places), tailgating (following an employee "
            "through a secure door without their own badge), and impersonation (posing as IT staff, a vendor, "
            "or a senior executive).\n\n"
            "Common examples: someone calling and claiming to be 'from head office' needing an urgent password "
            "reset, a stranger asking an employee to hold the door to a secure area, and an unfamiliar USB "
            "drive left in the break room labeled 'Salaries 2024.'"
        ),
        'scenario': (
            "A person you don't recognize approaches you in the office lobby, dressed professionally and "
            "carrying a clipboard. They say they're from 'corporate IT audit' and need you to walk them "
            "through the server room, claiming your usual badge reader is being tested and isn't working "
            "today."
        ),
        'questions': [
            {
                'question_text': 'What social engineering technique is being used here?',
                'option_a': 'Baiting',
                'option_b': 'Impersonation/pretexting',
                'option_c': 'Smishing',
                'option_d': 'Vishing',
                'correct_option': 'b',
            },
            {
                'question_text': 'What should you do in this situation?',
                'option_a': 'Let them in since they seem professional',
                'option_b': 'Verify their identity through official channels before granting any access',
                'option_c': 'Ask a coworker to escort them instead',
                'option_d': "Assume it's fine since they mentioned IT audit",
                'correct_option': 'b',
            },
            {
                'question_text': "Why is 'tailgating' into secure areas a security risk?",
                'option_a': 'It slows down foot traffic',
                'option_b': 'It allows unauthorized people to bypass physical access controls',
                'option_c': "It's only a minor inconvenience",
                'option_d': "It's not actually a security risk",
                'correct_option': 'b',
            },
            {
                'question_text': 'Finding an unlabeled USB drive in the office, you should:',
                'option_a': 'Plug it in to see what\'s on it',
                'option_b': 'Give it to IT/security without plugging it in',
                'option_c': 'Take it home',
                'option_d': 'Ignore it completely',
                'correct_option': 'b',
            },
            {
                'question_text': 'Social engineering attacks primarily exploit:',
                'option_a': 'Software vulnerabilities',
                'option_b': 'Human psychology and trust',
                'option_c': 'Network hardware flaws',
                'option_d': 'Encryption weaknesses',
                'correct_option': 'b',
            },
        ],
    },
    {
        'title': 'Building Strong Password Habits',
        'category': 'password_security',
        'description': 'Simple habits that dramatically reduce your risk of account compromise.',
        'content': (
            "Weak or reused passwords are one of the most common causes of account compromise. A strong "
            "password is long (at least 12 characters), unique to each account, and not based on easily "
            "guessable personal information like birthdays or pet names.\n\n"
            "Password managers allow you to use a different strong password for every account without needing "
            "to memorize them all. Multi-factor authentication (MFA) adds a second layer of protection, so "
            "even if a password is stolen, an attacker still can't log in without the second factor.\n\n"
            "Common mistakes: reusing the same password across work and personal accounts, writing passwords "
            "on sticky notes, and sharing passwords over chat or email 'just this once.'"
        ),
        'scenario': (
            "A colleague messages you on Slack asking to borrow your login for a shared reporting tool 'just "
            "for five minutes' because their account is locked and they have a deadline in ten minutes."
        ),
        'questions': [
            {
                'question_text': 'What should you do in this situation?',
                'option_a': "Share your password since it's urgent",
                'option_b': 'Decline and direct them to IT for an account reset instead',
                'option_c': 'Share it but change it right after',
                'option_d': "Ask them to promise not to change anything",
                'correct_option': 'b',
            },
            {
                'question_text': 'Why is password reuse across accounts risky?',
                'option_a': 'It saves time',
                'option_b': 'If one account is breached, all accounts using that password become vulnerable',
                'option_c': 'It has no real risk',
                'option_d': 'It is required by most companies',
                'correct_option': 'b',
            },
            {
                'question_text': 'What makes multi-factor authentication (MFA) effective?',
                'option_a': 'It replaces the need for a password entirely',
                'option_b': 'It requires a second proof of identity even if the password is stolen',
                'option_c': 'It makes login slower for no benefit',
                'option_d': 'It is only useful for banking apps',
                'correct_option': 'b',
            },
            {
                'question_text': 'A strong password is best described as:',
                'option_a': 'Short and easy to remember',
                'option_b': 'Long, unique per account, and not based on personal info',
                'option_c': 'The same one used everywhere for consistency',
                'option_d': 'Based on your birthday for easy recall',
                'correct_option': 'b',
            },
            {
                'question_text': 'Writing your password on a sticky note on your monitor is:',
                'option_a': 'A good backup method',
                'option_b': 'A physical security risk since anyone nearby can see it',
                'option_c': "Fine as long as it's a strong password",
                'option_d': 'Recommended by most IT departments',
                'correct_option': 'b',
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seeds 5 complete training modules with their quiz questions (safe to re-run).'

    def handle(self, *args, **options):
        modules_created = 0
        questions_created = 0

        for spec in MODULES:
            if TrainingModule.objects.filter(title=spec['title']).exists():
                self.stdout.write(f"  Skipping (already exists): {spec['title']}")
                continue

            module = TrainingModule.objects.create(
                title=spec['title'],
                category=spec['category'],
                description=spec['description'],
                content=spec['content'],
                scenario=spec['scenario'],
            )
            modules_created += 1
            self.stdout.write(f"  Created module: {module.title}")

            for q in spec['questions']:
                QuizQuestion.objects.create(
                    module=module,
                    question_text=q['question_text'],
                    option_a=q['option_a'],
                    option_b=q['option_b'],
                    option_c=q['option_c'],
                    option_d=q['option_d'],
                    correct_option=q['correct_option'],
                )
                questions_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nSeed complete: {modules_created} modules created, {questions_created} questions created."
        ))
